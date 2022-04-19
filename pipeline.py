from pipeline_lib import Step, Pipeline
import numpy as np
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
            from skimage.filters.rank import minimum
            from skimage.morphology import disk
            from skimage.util import img_as_ubyte

            DsRed = gaussian(DsRed, 1)
            GFP = gaussian(GFP, 1)
            DsRed[minimum(img_as_ubyte(DsRed), disk(30)) > 80] = 0

            return DsRed, GFP

        @self.add_step
        @Step.of('all_coordinates')
        def find_granule_centers(DsRed):
            from skimage.feature import peak_local_max
            import numpy as np
            coordinates = peak_local_max(DsRed, min_distance=15,
                                         threshold_abs=0.6)
            return list(coordinates)

        @self.add_step
        @Step.of(['DsRed', 'distances'])
        def flood_granule_areas(DsRed, all_coordinates):
            from custom_algo import multi_flood
            import numpy as np
            labels, distances, counts = multi_flood(DsRed, np.array(all_coordinates), mask=DsRed > 0.5)
            distances = distances - 1
            labels[distances == -1] = -1
            return labels, distances

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
        @Step.of(['rings_searched', 'rings_found', 'good_coordinates', 'good_granules', 'bad_coordinates', 'bad_granules'])
        def analyze_coordinates(all_coordinates, DsRed, GFP):
            from skimage.morphology import disk, dilation, erosion, skeletonize, thin
            import numpy as np

            good_coordinates = []
            bad_coordinates = []
            bad_floods = np.zeros_like(DsRed)
            good_floods = np.zeros_like(DsRed)
            all_floods = np.zeros_like(DsRed)
            rings_searched = np.zeros_like(DsRed)
            rings_found = np.zeros_like(DsRed)
            print('.' * (len(all_coordinates) // 10 - len("[x/x] Executing step extract_coordinates...") + 1))
            for i, coord in enumerate(all_coordinates):
                if i % 10 == 0:
                    print('.', end='')
                x, y = coord
                if bad_floods[x, y]:
                    bad_coordinates.append(coord)
                else:
                    current_flood = DsRed == i
                    masked = np.zeros_like(DsRed, dtype=float)
                    masked[current_flood] = 1

                    w = 35
                    h = 35

                    if x < w or x+w >= DsRed.shape[0] or y < h or y + h >= DsRed.shape[1]:
                        continue

                    def clip(large):
                        clipped = np.zeros((2*w, 2*h), dtype=large.dtype)
                        clipped[0:2*w, 0:2*h] = large[x-w:x+w, y-h:y+h]
                        return clipped

                    def unclip(clipped, background=None):
                        if background is None:
                            background = np.zeros_like(DsRed, dtype=clipped.dtype)
                        else:
                            background = np.copy(background)
                        background[x-w:x+w, y-h:y+h] = clipped[0:2*w, 0:2*h]
                        return background

                    # print()
                    # print(f"({x},___) --> ({np.average(np.arange(0, masked.shape[0])[masked[:, y] > 0])},{y})")
                    # print(f"(___,{y}) --> ({x},{np.average(np.arange(0, masked.shape[1])[masked[x, :] > 0])})")

                    masked = clip(masked)
                    all_floods[unclip(masked) > 0] = 1

                    # inner_avg = np.average(GFP[unclip(masked) > 0])

                    masked = dilation(masked, disk(3))
                    masked = dilation(masked, disk(3)) - masked
                    rings_searched[unclip(masked) > 0] = 1
                    # ring_avg = np.average(GFP[unclip(masked) > 0])

                    masked = np.minimum(clip(GFP), masked)
                    masked = masked > 0

                    if masked.size == 0:
                        bad_coordinates.append(coord)
                        # not touching bad_floods
                        continue

                    masked = thin(masked)
                    count = np.sum(masked)
                    rings_found[unclip(masked) > 0] = count

                    if count > 30:
                        good_coordinates.append(coord)
                        good_floods[current_flood] = 1
                    else:
                        bad_coordinates.append(coord)
                        bad_floods[current_flood] = 1

            return rings_searched, rings_found, good_coordinates, good_floods, bad_coordinates, bad_floods

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
                if self.find_step('extract_coordinates')._completed.is_set():
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
    stat_text, good_coordinates, bad_coordinates, all_coordinates = pipeline.run(
        ['stat_text', 'good_coordinates', 'bad_coordinates', 'all_coordinates'])

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
