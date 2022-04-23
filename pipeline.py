from pipeline_lib import Step, Pipeline
import numpy as np
import math
from copy import deepcopy


# helper function for reading a specified channel as numpy array (image)
def chreader(fname_template: str):
    def chread(chnum):
        from skimage.io import imread
        fname = fname_template.format(chnum)
        try:
            img = imread(fname)
            return img
        except FileNotFoundError:
            return None

    return chread


class RingDetector(Pipeline):
    def _add_to_img5(self, step, pipeline, state, completed=False, step_index=0, *args, **kwargs):
        import numpy as np

        outputs = ['DsRed', 'GFP', 'd', 'dd']
        shape = (1040, 1388)

        if completed:
            images5 = []
            for c, out in enumerate(outputs):
                if out in state:
                    img = deepcopy(state[out])
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
            from os import path
            from list_targets import default_dataset
            dataset_options = load(path.join(default_dataset, 'dataset.toml'))
            DsRed = chread(dataset_options['channels']['DsRed'])
            GFP = chread(dataset_options['channels']['GFP'])
            DAPI = chread(dataset_options['channels']['DAPI'])

            return DsRed, GFP, DAPI

        @self.add_step
        @Step.of(['DsRed', 'GFP'])
        def clean(DsRed, GFP):
            from skimage.filters import gaussian
            from skimage.filters.rank import minimum
            from skimage.morphology import disk
            from skimage.util import img_as_ubyte
            from skimage.exposure import adjust_gamma

            DsRed = gaussian(DsRed, 1)
            GFP = gaussian(GFP, 1)
            DsRed[minimum(img_as_ubyte(DsRed), disk(30)) > 80] = 0

            # DsRed = adjust_gamma(DsRed, 5)

            return DsRed, GFP

        @self.add_step
        @Step.of(['edges_h', 'edges_v', 'edges', 'edges_colorful'],
                 description="Edge detection using Sobel's algorithm")
        def edge_detect(DsRed):
            from skimage.filters import sobel_h, sobel_v, sobel
            from skimage.color import hsv2rgb

            h, v, grayscale = sobel_h(DsRed), sobel_v(DsRed), sobel(DsRed)
            colorful = hsv2rgb(np.dstack([
                np.arctan2(h, v) / math.pi / 2 + (np.arctan2(h, v) < 0) * 1,
                # np.sqrt(0.05 - (h*h+v*v)),
                # grayscale / np.max(grayscale),
                np.ones_like(grayscale),
                np.minimum(grayscale, np.ones_like(grayscale))]))
            # colorful = np.dstack([
            #     np.abs(h),
            #     np.abs(v),
            #     np.abs(v),
            # ])
            # colorful[:, :, 1][v < 0] = 0
            # colorful[:, :, 2][v > 0] = 0

            return h, v, grayscale, colorful

        @self.add_step
        @Step.of(['edges_h_abs', 'edges_v_abs', 'edges_angle'])
        def edge_abs(edges_h, edges_v):
            return np.abs(edges_h),\
                   np.abs(edges_v),\
                   np.arctan2(edges_h, edges_v) / math.pi / 2 + (np.arctan2(edges_h, edges_v) < 0) * 1

        # @self.add_step
        @Step.of(['dd_h', 'dd_v', 'dd', 'dd_colorful'])
        def edge_second_derivative(edges):
            from skimage.filters import sobel_h, sobel_v, sobel
            from skimage.color import hsv2rgb

            h, v, grayscale = sobel_h(edges), sobel_v(edges), sobel(edges)
            colorful = hsv2rgb(np.dstack([
                np.arctan2(h, v) / math.pi / 2 + (np.arctan2(h, v) < 0) * 1,
                np.ones_like(grayscale),
                np.minimum(grayscale, np.ones_like(grayscale))]))

            return h, v, grayscale, colorful
        
        # @self.add_step
        @Step.of(['dd_h_abs', 'dd_v_abs', 'dd_angle'])
        def dd_abs(dd_h, dd_v):
            return np.abs(dd_h),\
                   np.abs(dd_v),\
                   np.arctan2(dd_h, dd_v) / math.pi / 2 + (np.arctan2(dd_h, dd_v) < 0) * 1

        # @self.add_step
        @Step.of(['ddd', 'angle_diff'])
        def ddd(edges, edges_angle, dd, dd_angle):
            return {
                'ddd': np.abs(dd - edges),
                'angle_diff': np.abs(edges_angle - dd_angle),
            }

        @self.add_step
        @Step.of('all_coordinates')
        def find_granule_centers(DsRed):
            from skimage.feature import blob_doh
            coordinates = blob_doh(DsRed, threshold=0.001, min_sigma=2, max_sigma=5)
            return list(coordinates)

        @self.add_step
        @Step.of(['GFP'])
        def threshold(GFP):
            from skimage.morphology import disk
            from skimage.util import img_as_float, img_as_ubyte
            from skimage.filters.rank import mean, percentile
            from skimage.filters import threshold_local
            import numpy as np

            selem = disk(8)
            # GFP = img_as_ubyte(GFP)
            # th = mean(GFP, selem)
            # mean_mask = th < percentile(GFP, selem, p0=0.75)
            # th[mean_mask] = ((percentile(GFP, selem, p0=0.75) + th) / 2)[mean_mask]
            th = threshold_local(GFP, 15, offset=-0.01)
            # th = img_as_float(th)
            # GFP = img_as_float(GFP)
            return GFP - th,

        @self.add_step
        @Step.of(['rings_searched', 'all_granules',
                  'rings_expected', 'rings_found', 'rings_too_small',
                  'good_coordinates', 'good_granules', 'bad_coordinates', 'bad_granules'])
        def analyze_coordinates(all_coordinates, edges, edges_angle, GFP):
            gfp_bin = GFP > 0

            def process_granule(o, r=15):
                import scipy.ndimage as ndi
                from skimage.measure import label, regionprops

                def clip_shapes(img):
                    xf = int(o[0] - r)
                    xt = int(o[0] + r + 1)
                    yf = int(o[1] - r)
                    yt = int(o[1] + r + 1)
                    xfc = -xf if xf < 0 else 0
                    yfc = -yf if yf < 0 else 0
                    xtc = 0 if xt < img.shape[0] else img.shape[0] - xt - 1
                    ytc = 0 if yt < img.shape[1] else img.shape[1] - yt - 1
                    return (xf, xt, yf, yt), (xfc, xtc, yfc, ytc)

                def clip(img):
                    (xf, xt, yf, yt), (xfc, xtc, yfc, ytc) = clip_shapes(img)
                    result = np.zeros((2*r+1, 2*r+1), dtype=img.dtype)
                    result[xfc:2*r+1+xtc, yfc:2*r+1+ytc] = img[xf+xfc:xt+xtc, yf+yfc:yt+ytc]
                    return result

                def unclip(img):
                    (xf, xt, yf, yt), (xfc, xtc, yfc, ytc) = clip_shapes(edges)
                    result = np.zeros_like(edges, dtype=img.dtype)
                    result[xf+xfc:xt+xtc, yf+yfc:yt+ytc] = img[xfc:2*r+1+xtc, yfc:2*r+1+ytc]
                    return result

                def process_projection(magnitude, angle, p=60):
                    from skimage.filters import threshold_isodata

                    sample_angle = np.fromfunction(lambda x, y: np.arctan2(x - r, y - r) / math.pi / 2, (2 * r + 1, 2 * r + 1))
                    angle_diff = angle - sample_angle + (sample_angle > angle) * 1
                    angle_diff[angle_diff > 0.5] -= 1
                    angle_diff = (0.5 - np.abs(angle_diff)) / 0.5

                    mul = (1 - angle_diff) * magnitude

                    # magnitude_limit = np.percentile(magnitude, p)
                    # angle_diff_limit = 0.5
                    # mask = (magnitude > magnitude_limit) * (angle_diff < angle_diff_limit)
                    # mask = mul > np.percentile(mul, 0.75)
                    mask = mul > threshold_isodata(mul)

                    return mask, mul, angle_diff

                lumen_mask, lumen_prob, _ = process_projection(clip(edges), clip(edges_angle))
                lumen_labels, lumen_count = label(lumen_mask, return_num=True)

                best_lumen_regionprop = None
                for regionprop in regionprops(lumen_labels, lumen_prob):
                    def dist(regionprop):
                        x, y = regionprop.centroid
                        x -= r + 1
                        y -= r + 1
                        return math.sqrt(x * x + y * y)

                    if best_lumen_regionprop is None:
                        best_lumen_regionprop = regionprop
                    elif dist(best_lumen_regionprop) > dist(regionprop):
                        best_lumen_regionprop = regionprop

                lumen_convex = np.zeros_like(lumen_mask, dtype=np.bool)
                lumen_convex[
                best_lumen_regionprop.bbox[0]:best_lumen_regionprop.bbox[2],
                best_lumen_regionprop.bbox[1]:best_lumen_regionprop.bbox[3]] =\
                    best_lumen_regionprop.image_convex

                from skimage.morphology import binary_erosion, disk
                membrane = lumen_convex * ~binary_erosion(lumen_convex) * lumen_mask

                membrane = binary_dilation(membrane, disk(3))

                masked = clip(gfp_bin)
                masked[~membrane] = False
                masked = thin(masked)

                fake_masked = membrane.copy()
                fake_masked = thin(fake_masked)

                is_good = np.sum(masked) > np.sum(fake_masked) / 2

                return unclip(lumen_convex), unclip(membrane), unclip(masked), unclip(fake_masked), is_good

            good_coordinates = []
            bad_coordinates = []
            lumens = np.zeros_like(edges)
            good_lumens = np.zeros_like(edges)
            bad_lumens = np.zeros_like(edges)
            membrane_areas = np.zeros_like(edges)
            membranes = np.zeros_like(edges)
            good_membranes = np.zeros_like(edges)
            bad_membranes = np.zeros_like(edges)
            # print('_' * (len(all_coordinates) // 100 + 1))
            for i, coords in enumerate(all_coordinates):
                from skimage.morphology import disk, binary_dilation, thin

                # if i % 100 == 0:
                #     print('.', end='')

                x, y = coords
                r = 15
                lumens[int(x), int(y)] += 1

                process_result = process_granule((x, y), int(r + 5))
                if process_result is not None:
                    lumen, membrane, ring, fake_ring, is_good = process_result

                    if lumen is not None:
                        lumens[lumen] += 1

                    if membrane is not None:
                        membrane_areas[membrane] += 1

                    if fake_ring is not None:
                        membranes[fake_ring] += 1

                    if is_good is not None:
                        if is_good:
                            good_coordinates.append(coords)
                            good_lumens[lumen] += 1
                            good_membranes[ring] += 1
                        else:
                            bad_coordinates.append(coords)
                            bad_lumens[lumen] += 1
                            bad_membranes[ring] += 1

            print()
            return {
                'rings_searched': membrane_areas,
                'rings_expected': membranes,
                'rings_found': good_membranes,
                'rings_too_small': bad_membranes,
                'all_granules': lumens,
                'good_coordinates': good_coordinates,
                'good_granules': good_lumens,
                'bad_coordinates': bad_coordinates,
                'bad_granules': bad_lumens,
            }

        @self.add_step
        @Step.of('stat_text')
        def count(all_coordinates, good_coordinates, bad_coordinates):
            stat_text = []
            stat_text.append(f"Count: {len(all_coordinates)}\n")
            stat_text.append(f"Hit count: {len(good_coordinates)}\n")
            stat_text.append(f"Miss count: {len(bad_coordinates)}\n")
            stat_text.append(f"Ratio: {len(good_coordinates) / (len(good_coordinates) + len(bad_coordinates))}\n")
            return stat_text

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

        # Show captured step-intermediate images using View 5D
        viewer = NanoImagingPack.v5(np.array(self._img5), multicol=True)
        # note: using img4 instead of img5 is a good idea

        # Navigate to the output of step 1 and initialize exposure
        viewer.ProcessKeys(',,,T')

        # Displaying the coordinates

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

        if self.find_step('extract_coordinates')._completed.is_set():
            # Pushing the coordinates to the user interface (good -> List1, bad -> List2)
            viewer.setMarkers(f(self.state['good_coordinates']), 1)
            viewer.setMarkers(f(self.state['bad_coordinates']), 2)

            # Set marker colors (List1 -> green, List2 -> blue)
            myMarkerLists = jb.get_field(my3DData, 'MyMarkers', 'Lview5d/MarkerLists;')
            jb.call(jb.call(myMarkerLists, 'GetMarkerList', '(I)Lview5d/MarkerList;', 1), 'SetColor', '(I)V', 0x00FF00)
            jb.call(jb.call(myMarkerLists, 'GetMarkerList', '(I)Lview5d/MarkerList;', 2), 'SetColor', '(I)V', 0x0000FF)

        # Refresh UI by initializing viewport
        viewer.ProcessKeys('i')


def run_application(fname_template, folder=None, interactive=False):
    from os.path import dirname
    import sys

    pipeline = RingDetector(fname_template, interactive=interactive)
    stat_text, = pipeline.run(['stat_text'])

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
