from pipeline_lib import Step, Pipeline
import numpy as np


# helper function for reading a specified channel as numpy array (image)
def chreader(fname_template: str):
    def chread(chnum):
        from skimage.io import imread
        fname = fname_template.format(chnum)
        img = imread(fname)
        return img

    return chread


class RingDetector(Pipeline):
    def _add_to_img5(self, step, pipeline, state, completed=False, step_index=0, *args, **kwargs):
        import numpy as np

        outputs = ['DsRed', 'GFP', 'DAPI']
        shape = (1040, 1388)

        if completed:
            images5 = []
            for c, out in enumerate(outputs):
                if out in state:
                    img = state[out].copy()
                else:
                    img = np.zeros(shape)
                images5.append([img])
            self._img5.append(images5)

    def __init__(self, fname_template=None, chread=None, interactive=False):
        super().__init__()
        self.seal_steps()
        self._img5 = []
        self._interactive = interactive

        if chread is None:
            chread = chreader(fname_template)

        if chread is None:
            raise RuntimeError("Either supply chread of fname_template")

        @self.add_step
        @Step.of(['DsRed', 'GFP', 'DAPI'])
        def load():
            from toml import load
            dataset_options = load('képek/dataset.toml')
            DsRed = chread(dataset_options['channels']['DsRed'])
            GFP = chread(dataset_options['channels']['GFP'])
            DAPI = chread(dataset_options['channels']['DAPI'])

            return DsRed, GFP, DAPI

        @self.add_step
        @Step.of(['DsRed', 'GFP'])
        def clean(DsRed, GFP):
            from skimage.filters import gaussian

            DsRed = gaussian(DsRed, 1)
            GFP = gaussian(GFP, 1)
            # TODO median proba

            return DsRed, GFP

        @self.add_step
        @Step.of(['DsRed', 'GFP'])
        # Extracting circular features - converting disks to circles
        def circlize(DsRed, GFP):
            from skimage.morphology import erosion, dilation, disk
            from skimage.filters import threshold_local

            # Regions in GFP under granules can't be considered meaningful, masking them out to NaN
            GFP[erosion(DsRed, disk(2)) > threshold_local(erosion(DsRed, disk(2)), 19, 'median')] = np.nan

            # Extracting the granule membranes
            DsRed = dilation(DsRed, disk(3)) - erosion(DsRed, disk(1))

            return DsRed, GFP

        # TODO skip this step for more accuracy
        #      needs replacing hough_circle with custom algo
        @self.add_step
        @Step.of(['DsRed', 'GFP'])
        # Converting grayscale images to binary images, essentially thresholding
        # Instead of returning True/False values, returns an image, where black means False and the original value means True
        def binarize(DsRed, GFP):
            from skimage.filters.rank import percentile
            from skimage.morphology import disk, binary_opening
            from skimage.util import img_as_ubyte, img_as_float

            # DsRed has no exposure variance; thresholding over the average is enough
            DsRed_bin = DsRed > np.average(DsRed)

            # GFP is a bit trickier: A pixel is kept, if its value is greater than
            # the 75th percentile in its 40x40 circular neighbourhood
            GFP_bin = GFP > img_as_float(percentile(img_as_ubyte(GFP), disk(20), p0=0.75))

            # Setting the actual return values (=0 or >0)
            DsRed[~DsRed_bin] = 0
            GFP[~GFP_bin] = 0

            return DsRed, GFP

        @self.add_step
        @Step.of('GFP')
        # Applies the mask of DsRed to GFP - used to filter out false positives
        def binary_mask(DsRed, GFP):
            GFP[DsRed == 0] = 0

            return GFP

        @self.add_step(details="being debugged")
        @Step.of(['DsRed', 'GFP'])
        # Simple hough transformation
        def hough(DsRed, GFP):
            from skimage.transform import hough_circle

            # Since the size of the granule is unknown, trying multiple radiuses
            radius = np.arange(8, 15)

            # Applying binary hough transformation to both DsRed and GFP
            DsRed = np.amax(hough_circle(DsRed, radius), axis=0)
            GFP = np.amax(hough_circle(GFP, radius), axis=0)

            # Making intenser values more intense by squaring the images
            DsRed = DsRed ** 2
            GFP = GFP ** 2

            return DsRed, GFP

        @self.add_step
        @Step.of(['stat_text', 'stat_image'])
        def calc(DsRed, GFP):
            stat_text = []
            if fname_template is not None:
                stat_text.append(f"fname_template: {fname_template}\n")
            stat_text.append(f"Scalar ratio: {np.sum(GFP.astype(np.float64)) / np.sum(DsRed.astype(np.float64))}\n")
            stat_text.append(f"Scalar positives: {np.average(GFP.astype(np.float64))}\n")

            stat_image = GFP * 2 - DsRed
            stat_image[stat_image < 0] = 0
            stat_text.append(f"Stat: {np.average(stat_image)}\n")

            # Instead of saving just the stat, also add the final DsRed and GFP channels for further inspection
            stat_image = np.dstack([DsRed, GFP, stat_image])

            return stat_text, stat_image

        @self.add_step
        @Step.of(['good_coordinates', 'bad_coordinates', 'all_coordinates'])
        def find_coordinates(DsRed, GFP):
            # Helper function to locate circle centers after hough transformation
            def extract_coordinates(img, *masks):
                """
                Creates a list of peak coordinates from an image and a list of masks

                :param img: Image to search peak values on
                :param masks: Array of (img, threshold, invert_threshold) tuples
                :return: list of (x, y) tuples
                """
                from skimage.feature import peak_local_max
                coords = peak_local_max(img, min_distance=15)
                mask = np.ones_like(img) > 0
                while len(masks) > 0:
                    from skimage.filters.rank import maximum
                    from skimage.morphology import disk
                    from skimage.util import img_as_ubyte, img_as_float

                    # shift the current mask to (mask_img, th, invert_th)
                    mask_img, th, invert_th = masks[0] + (img, 0.5, False)[len(masks[0]):]
                    masks = masks[1:]

                    mask_img = np.minimum(np.maximum(mask_img,
                                                     np.zeros_like(img)),
                                          np.ones_like(img))
                    mask_img = img_as_float(maximum(img_as_ubyte(mask_img), disk(5)))
                    bin = mask_img > th
                    if invert_th:
                        bin = ~bin
                    mask[~bin] = False

                coords = filter(lambda coord: mask[coord[0], coord[1]], coords)
                coords = list(coords)
                return coords

            # Good coordinates are circle centers on DsRed, where there is a nearby circle center (DsRed) value at least 0.5 and
            # there is a nearby GFP value at least 0.35
            good_coordinates = extract_coordinates(DsRed, (), (GFP, 0.35, False))

            # Bad coordinates are similar to good coordinates, but the GFP mask is flipped
            bad_coordinates = extract_coordinates(DsRed, (), (GFP, 0.35, True))

            # All coordinates do not have any GFP filter
            all_coordinates = extract_coordinates(DsRed, ())

            return good_coordinates, bad_coordinates, all_coordinates

        @self.add_step
        @Step.of('stat_text')
        def count(stat_text, good_coordinates, bad_coordinates, all_coordinates):
            stat_text.append(f"Count: {len(all_coordinates)}\n")
            stat_text.append(f"Hit count: {len(good_coordinates)}\n")
            stat_text.append(f"Miss count: {len(bad_coordinates)}\n")
            stat_text.append(f"Ratio: {len(good_coordinates) / len(all_coordinates)}\n")
            return stat_text

        if interactive:
            # Interactive mode has two more, kinda useless steps, only for demonstration purposes

            @self.add_step
            @Step.of(['DsRed', 'GFP'])
            # If we blur the image, the misaligned GFP and DsRed centers are displayed on the same pixel,
            # thus we can tell using a human eye much more of a given pixel by its lightness and its hue
            def blur(DsRed, GFP):
                from skimage.filters import gaussian

                sigma = 15
                DsRed = gaussian(DsRed, sigma)
                GFP = gaussian(GFP, sigma)

                return DsRed, GFP

            @self.add_step
            @Step.of('ratio')
            # Replaces the whole display with a grayscale image of "good" regions
            def visual_calc(DsRed, GFP):
                ratio = GFP * 1.5 - DsRed
                ratio[ratio < 0] = 0

                return ratio

        self.seal_steps()

    def _hook(self, hook, *args, **kwargs):
        if self._interactive:
            self._add_to_img5(*args, **kwargs)

        super(RingDetector, self)._hook(hook, *args, **kwargs)

    def view_in_5d(self, step=None, step_index=0):
        if not step:
            step = None

        img5 = []
        markers = []
        commands = ''

        if step is None:
            if self._interactive:
                img5 = self._img5
                commands = ',T'
                # commands = ',,,,,vET'
                #
                if self.find_step('find_coordinates')._completed.is_set():
                    markers = [
                        (self.state['good_coordinates'], 0x00FF00),
                        (self.state['bad_coordinates'], 0x0000FF),
                    ]
            else:
                raise RuntimeError("Not started interactively")
        else:
            shape = (1040, 1388)
            marker_size = 15
            step = self.find_step(step, step_index)

            def transform_data(data):
                img = np.zeros(shape)
                if isinstance(data, np.ndarray):
                    img = data
                if isinstance(data, list):
                    for (x, y) in data:
                        img[x-marker_size:x+marker_size, y-marker_size:y+marker_size] = 1
                    markers.append((data, None))
                return [img]

            if step._completed.is_set():
                img5 = list(map(transform_data, step.last_output.values()))
            elif step._started.is_set():
                img5 = list(map(transform_data, step.last_input.values()))

        import NanoImagingPack

        viewer = NanoImagingPack.v5(np.array(img5), multicol=True if step is None else None)
        viewer.ProcessKeys(commands)

        import javabridge as jb

        my3DData = jb.get_field(viewer.o, 'data3d', 'Lview5d/My3DData;')
        myMarkerLists = jb.get_field(my3DData, 'MyMarkers', 'Lview5d/MarkerLists;')

        jb.set_field(my3DData, 'ConnectionShown', 'Z', False)

        # Helper function: Converts 2D coordinates to 5D, spanning all steps
        def f(coords):
            result = []
            for coord in coords:
                for t in range(len(self.steps)):
                    result.append(np.array([t, 0, 0, coord[0], coord[1]]))
            return result

        for i, (l, c) in enumerate(markers):
            viewer.setMarkers(f(l), i + 1)
            if c is not None:
                jb.call(jb.call(myMarkerLists, 'GetMarkerList', '(I)Lview5d/MarkerList;', i + 1), 'SetColor', '(I)V', c)

        # Refresh UI by initializing viewport
        viewer.ProcessKeys('i')


def run_application(fname_template, folder=None, interactive=False):
    from os.path import dirname
    import sys

    pipeline = RingDetector(fname_template, interactive=interactive)
    stat_text, good_coordinates, bad_coordinates, all_coordinates, stat_image = pipeline.run(
        ['stat_text', 'good_coordinates', 'bad_coordinates', 'all_coordinates', 'stat_image'])

    if interactive:
        print()
        print("Statistics:")
        sys.stdout.writelines(stat_text)
        print()
        pipeline.view_in_5d()
        print("done")
    else:
        if folder is None:
            folder = dirname(fname_template)

        # In non-interactive mode saving all output to the folder given by CLI argument
        open(folder + '/stats.txt', 'w').writelines(stat_text)
        open(folder + '/granules-with-rings.txt', 'w').writelines(
            ['\t'.join(map(str, reversed(coord))) + '\n' for coord in good_coordinates])
        open(folder + '/granules-without-rings.txt', 'w').writelines(
            ['\t'.join(map(str, reversed(coord))) + '\n' for coord in bad_coordinates])
        open(folder + '/granules.txt', 'w').writelines(
            ['\t'.join(map(str, reversed(coord))) + '\n' for coord in all_coordinates])

        from skimage.io import imsave
        from skimage.util import img_as_ubyte

        # Sometimes stat values are out of range; fixing
        stat_image[stat_image > 1] = 1
        stat_image[stat_image < 0] = 0

        imsave(folder + '/stats.tif', img_as_ubyte(stat_image))


def main(argv, stderr):
    fname_template = "GlueRab7_ctrl_-2h-0021.tif_Files/GlueRab7_ctrl_-2h-0021_c{}.tif"
    # fname_template = "képek/GF-0h-2022.2.10/GF_0h-0009.tif_Files/GF_0h-0009_c{}.tif"
    folder = None

    if len(argv) > 1:
        fname_template = argv[1]
    if len(argv) > 2:
        folder = argv[2]

    interactive = len(argv) < 3
    if interactive:
        print(f"Usage: {argv[0]} input_template [output_folder | \"\"]", file=stderr)
        print("For non-interactive usage please supply both arguments", file=stderr)

    run_application(fname_template, folder or None, interactive)


if __name__ == '__main__':
    import sys
    main(sys.argv, sys.stderr)
