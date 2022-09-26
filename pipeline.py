import os

from tqdm import tqdm

from list_targets import Target, CustomTarget, RgbTarget
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

    @Step.of(['DsRed', 'GFP', 'mask'])
    def clean(self, DsRed, GFP):
        from skimage.filters import gaussian
        DsRed_blurred = gaussian(DsRed)
        GFP_blurred = gaussian(GFP)
        mask = np.ones_like(DsRed, dtype=np.bool)
        # mask[DsRed_blurred < 0.2] = 0
        DsRed = gaussian(DsRed)
        GFP = gaussian(GFP)
        DsRed[~mask] = 0
        GFP[~mask] = 0
        return DsRed, GFP, mask

    # @Step.of(['diff', 'diff_abs'])
    # def diff(self, DsRed, GFP):
    #     diff = GFP - DsRed
    #     return diff, np.abs(diff)
    #
    # @Step.of('sum')
    # def sum(self, DsRed, GFP):
    #     return GFP / 2 + DsRed / 2

    @Step.of('all_coordinates')
    def find_granule_centers(self, DsRed):
        from skimage.feature import blob_dog as blob
        coordinates = blob(DsRed, min_sigma=7, max_sigma=10, threshold=0.01, overlap=1)
        return list(map(lambda a: (int(a[0]), int(a[1]), int(a[2])), list(coordinates)))

    @Step.of('marked')
    def fill_holes(self, DAPI):
        DAPI = DAPI > 128
        from scipy import ndimage as ndi
        return ndi.binary_fill_holes(DAPI)

    @Step.of('GFP')
    def threshold(self, GFP):
        from skimage.morphology import disk
        from skimage.util import img_as_float, img_as_ubyte
        from skimage.filters.rank import mean, percentile
        from skimage.filters import threshold_local, rank
        import numpy as np

        selem = disk(8)
        # GFP = img_as_ubyte(GFP)
        # th = mean(GFP, selem)
        # mean_mask = th < percentile(GFP, selem, p0=0.75)
        # th[mean_mask] = ((percentile(GFP, selem, p0=0.75) + th) / 2)[mean_mask]
        # th = threshold_local(GFP, 15, offset=-0.01)
        th = rank.otsu(GFP, selem) / 256
        # th = img_as_float(th)
        # GFP = img_as_float(GFP)
        return GFP < th

    @Step.of('model')
    def load_ai(self):
        from model import saved
        return saved.get()

    @Step.of(['positive_coordinates', 'neutral_coordinates', 'negative_coordinates',
              'fake_GFP', 'fake_membranes', 'expected_membranes', 'found_membranes', 'result'])
    def analyze_coordinates(self, model, all_coordinates, GFP, mask, DsRed, marked, DAPI):
        from skimage.draw import disk
        import tensorflow

        neutral = []
        gfp_positive = []
        gfp_negative = []
        fake_GFP = np.zeros_like(GFP, dtype=float)
        fake_membranes = np.zeros_like(GFP, dtype=bool)
        found_membranes = np.zeros_like(GFP, dtype=bool)
        expected_membranes = np.zeros_like(GFP, dtype=bool)
        result = np.zeros_like(GFP, dtype=float)
        for (i, coordinates) in tqdm(list(enumerate(all_coordinates))):
            x, y, r = coordinates
            granule_mask = np.zeros_like(GFP, dtype=bool)
            fr = 32
            if isinstance(self.target, RgbTarget) and marked[x, y]:
                try:
                    from skimage.io import imsave
                    from skimage.util import img_as_ubyte
                    input_frame = DsRed[x - fr:x + fr, y - fr:y + fr]
                    imsave(f"frames/frame_{i:03}.png", img_as_ubyte(input_frame))
                    input_frame = np.zeros_like(input_frame, dtype='uint8')
                    from skimage.morphology import flood_fill
                    input_frame[marked[x - fr:x + fr, y - fr:y + fr]] = 2
                    input_frame[DAPI[x - fr:x + fr, y - fr:y + fr] > 128] = 1
                    input_frame[flood_fill(marked[x - fr:x + fr, y - fr:y + fr].astype('uint8'), (fr, fr), 2, connectivity=1) != 2] = 0
                    imsave(f"frame_annotations/frame_{i:03}.png", img_as_ubyte(input_frame * fr))
                    gfp_positive.append(coordinates)
                except IndexError:
                    pass
            try:
                try:
                    from skimage.transform import resize
                    from skimage.color import gray2rgb
                    from skimage.io import imsave
                    from skimage.util import img_as_ubyte
                    from skimage.filters import threshold_otsu
                    from skimage.morphology import thin

                    frame_DsRed = DsRed[x - fr:x + fr, y - fr:y + fr]

                    frame_segmentation = model(frame_DsRed.reshape(1, 2 * fr, 2 * fr, 1))[0].numpy()
                    if (isinstance(self.target, RgbTarget)):
                        imsave(f"all_frames/frame_{i:03}_segmented.png", img_as_ubyte(frame_segmentation))

                    frame_membrane_pred = frame_segmentation[:, :, 1]
                    fake_GFP[x - fr:x + fr, y - fr:y + fr] += frame_membrane_pred

                    frame_membrane_pred = frame_membrane_pred > threshold_otsu(frame_membrane_pred)
                    fake_membranes[x - fr:x + fr, y - fr:y + fr][frame_membrane_pred] = True

                    expected_membranes[x - fr:x + fr, y - fr:y + fr] += thin(frame_membrane_pred)
                    expected_count = np.sum(thin(frame_membrane_pred))

                    frame_membrane_pred *= GFP[x - fr:x + fr, y - fr:y + fr] > 0
                    frame_membrane_pred = thin(frame_membrane_pred)

                    found_membranes[x - fr:x + fr, y - fr:y + fr] += frame_membrane_pred

                    score = np.sum(frame_membrane_pred) / expected_count
                    result[x - fr:x + fr, y - fr:y + fr] = np.maximum(frame_membrane_pred * score,
                                                                      result[x - fr:x + fr, y - fr:y + fr])

                    if score > 0.7:
                        gfp_positive.append(coordinates)
                    if score > 0.5:
                        neutral.append(coordinates)
                    else:
                        gfp_negative.append(coordinates)
                except ValueError as e:
                    # print(f"Skipping ({x},{y})")
                    pass

                from skimage.io import imsave
                from skimage.util import img_as_ubyte
                input_frame = DsRed[x - fr:x + fr, y - fr:y + fr]
                if isinstance(self.target, RgbTarget):
                    imsave(f"all_frames/frame_{i:03}.png", img_as_ubyte(input_frame))
            except ValueError as e:
                if f"{e}" == "zero-size array to reduction operation minimum which has no identity":
                    pass
                else:
                    print(f"Error ({e}) for #{i:03}")
            except IndexError:
                pass
        return gfp_positive, neutral, gfp_negative,\
               fake_GFP, fake_membranes, expected_membranes, found_membranes, result

    @Step.of('stat_text')
    def count(self, all_coordinates, positive_coordinates, neutral_coordinates, negative_coordinates):
        stat_text = []
        all = len(all_coordinates)
        neutral = len(neutral_coordinates)
        negative = len(negative_coordinates)
        positive = len(positive_coordinates)

        stat_text.append(f"Count: {all}\n")
        stat_text.append(f"GFP positive: {neutral}\n")
        stat_text.append(f"GFP negative: {negative}\n")
        stat_text.append(f"Invalid: {positive}\n")
        stat_text.append(f"Dropped: {(all - (neutral + negative)) / all :.2%}\n")
        stat_text.append(f"GFP negative ratio: {negative / (neutral + negative):.2%}\n")
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
                        img[x - marker_size:x + marker_size, y - marker_size:y + marker_size] = 1
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
