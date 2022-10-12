from list_targets import Target, CustomTarget
from pipeline_lib import Step, Pipeline
import numpy as np
import math
from copy import deepcopy


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

    @property
    def initial_state(self):
        return {'target': self.target}

    def __init__(self, target: Target, interactive=False):
        super().__init__()
        self._img5 = []
        self._interactive = interactive
        self.target = target

    @Step.of(['DsRed', 'GFP', 'DAPI'])
    def load(self, target):
        from toml import load
        from os import path
        dataset_options = load(path.join(target.dataset, 'dataset.toml'))
        DsRed = target.chread(dataset_options['channels']['DsRed'])
        GFP = target.chread(dataset_options['channels']['GFP'])
        DAPI = target.chread(dataset_options['channels']['DAPI'])

        return DsRed, GFP, DAPI

    @Step.of(['DsRed', 'GFP', 'mask', 'gfp_min'])
    def clean(self, DsRed, GFP, DAPI):
        from skimage.filters import gaussian
        from skimage.filters.rank import minimum
        from skimage.morphology import disk
        from skimage.util import img_as_ubyte, img_as_float
        DAPI = gaussian(DAPI, 5)
        DsRed_blurred = gaussian(DsRed)
        GFP_blurred = gaussian(GFP)
        mask = np.ones_like(DAPI, dtype=np.bool)
        mask[DAPI > 0.2] = 0
        mask[DsRed_blurred < 0.2] = 0
        DsRed = gaussian(DsRed)
        GFP = gaussian(GFP)
        gfp_min = img_as_float(minimum(img_as_ubyte(GFP), footprint=disk(30)))
        GFP = GFP - gfp_min
        DsRed[~mask] = 0
        GFP[~mask] = 0
        return DsRed, GFP, mask, gfp_min

    @Step.of(['diff', 'diff_abs'])
    def diff(self, DsRed, GFP):
        diff = GFP - DsRed
        return diff, np.abs(diff)

    @Step.of('sum')
    def sum(self, DsRed, GFP):
        return GFP / 2 + DsRed / 2

    @Step.of('all_coordinates')
    def find_granule_centers(self, sum):
        from skimage.feature import blob_dog as blob
        coordinates = blob(sum, min_sigma=7, max_sigma=10, threshold=0.01, overlap=1)
        return list(map(lambda a: (int(a[0]), int(a[1]), int(a[2])), list(coordinates)))

    @Step.of(['positive_coordinates', 'neutral_coordinates', 'negative_coordinates'])
    def analyze_coordinates(self, all_coordinates, diff, GFP, mask):
        from skimage.draw import disk

        neutral = []
        gfp_positive = []
        gfp_negative = []
        for coordinates in all_coordinates:
            x, y, r = coordinates
            granule_mask = np.zeros_like(diff, dtype=bool)
            try:
                xx, yy = disk((x, y), r)
                granule_mask[xx, yy] = True
                granule_mask = mask * granule_mask
                if np.mean(GFP, where=granule_mask) < 0.25:
                    gfp_negative.append(coordinates)
                # elif np.mean(diff, where=granule_mask) > 0.2:
                #     gfp_positive.append(coordinates)
                else:
                    neutral.append(coordinates)
            except IndexError:
                pass
        return gfp_positive, neutral, gfp_negative

    @Step.of('stat_text')
    def count(self, all_coordinates, positive_coordinates, neutral_coordinates, negative_coordinates):
        stat_text = []
        all = len(all_coordinates)
        neutral = len(neutral_coordinates)
        negative = len(negative_coordinates)
        positive = len(positive_coordinates)

        stat_text.append(f"Count: {all}\n")
        stat_text.append(f"Positive: {neutral}\n")
        stat_text.append(f"Negative: {negative}\n")
        stat_text.append(f"Invalid: {positive}\n")
        stat_text.append(f"Dropped: {(all - (neutral + negative)) / all :.2%}\n")
        stat_text.append(f"Negative ratio: {negative / (neutral + negative):.2%}\n")
        return stat_text

    @Step.on(['DsRed', 'all_coordinates', 'positive_coordinates', 'neutral_coordinates', 'negative_coordinates'],
             of=['all', 'positive', 'neutral', 'negative'])
    def visualize_coordinates(self, sample, *args):
        def visualize_list(l):
            from skimage.draw import disk
            img = np.zeros_like(sample)
            for x, y, r in l:
                xx, yy = disk((x, y), r)
                try:
                    img[xx, yy] = 1
                except IndexError:
                    img[x, y] = 1

            return img

        return list(map(visualize_list, args))

    @Step.of('save_path')
    def save_stats(self, target, stat_text):
        open(target.stats_path, 'w').writelines(stat_text)
        return target.stats_path

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
                        img[x - marker_size:x + marker_size, y - marker_size:y + marker_size] = 1
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

    run_application(CustomTarget(fname_template, folder), interactive=interactive)


if __name__ == '__main__':
    import sys

    main(sys.argv, sys.stderr)
