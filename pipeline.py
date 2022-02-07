import copy
import sys

import matplotlib.pyplot
import numpy as np

if len(sys.argv) > 1:
    fname_template = sys.argv[1]
else:
    # fname_template = "kepek/Új_Ub_ab/08_11_overnight_PBTXDoc/Uj_Ub_ab_2_-6h-0039.tif_Files/Uj_Ub_ab_2_-6h-0039_c{}.tif"
    # fname_template = "mCD8-GFP_GlueRed_-6h-0023_0_Z3_C{}_T0.tiff"
    fname_template = "GlueRab7_ctrl_-2h-0021.tif_Files/GlueRab7_ctrl_-2h-0021_c{}.tif"

if len(sys.argv) > 2:
    folder = sys.argv[2]

interactive = len(sys.argv) < 3
if interactive:
    print(f"Usage: {sys.argv[0]} input_template [output_template]", file=sys.stderr)
    matplotlib.use('QtAgg')
    # noinspection PyUnresolvedReferences
    import NanoImagingPack
    # noinspection PyUnresolvedReferences
    import bioformats


def chread(c):
    from skimage.io import imread
    fname = fname_template.format(c)
    img = imread(fname)
    return img


last = []
img5 = []
img4 = None
step_cnt = 0


def step(func):
    from inspect import signature
    global step_cnt, img5, img4
    print(f"Step {step_cnt}: {func.__name__} {signature(func)}", file=sys.stderr)
    params = signature(func).parameters
    result = func(*[copy.deepcopy(last[c]) if interactive else last[c] for c in range(len(params))])
    step_cnt += 1
    for c in range(len(result)):
        last[c] = result[c]

    images5 = []
    if img4 is None:
        img4 = [[] for _ in last]
    for c in range(len(last)):
        img = last[c].copy()
        # img[np.isnan(img)] = 0
        images5.append([img])
        img = img / np.max(img)
        img4[c].append(img)
    img5.append(images5)


def skip(func):
    f = lambda: ()
    f.__name__ = f"skipped ({func.__name__})"
    return f


@step
def load():
    global last, composite
    last = [chread(c) for c in range(2)]
    # composite = np.dstack(last)
    return last


@step
def clean(DsRed, GFP):
    from skimage.filters import gaussian
    from skimage.morphology import dilation
    from skimage.exposure import equalize_adapthist
    DsRed = gaussian(DsRed, 1)
    GFP = gaussian(GFP, 1)
    # TODO instead of equalize_adapthist, scale each 50x50px frame to its maximum to its lowest 25% percentile
    # GFP = equalize_adapthist(GFP)
    # ... or using local thresholding
    # GFP = dilation(GFP)
    return DsRed, GFP


@step
def circlize(DsRed, GFP):
    from skimage.morphology import erosion, dilation, disk
    from skimage.filters import threshold_local
    GFP[erosion(DsRed, disk(2)) > threshold_local(erosion(DsRed, disk(2)), 19, 'median')] = np.nan
    DsRed = dilation(DsRed, disk(3)) - erosion(DsRed, disk(1))
    return DsRed, GFP


# TODO skip this step for more accuracy
#      needs replacing hough_circle with custom algo
@step
def binarize(DsRed, GFP):
    from skimage.filters.rank import percentile
    from skimage.morphology import disk, binary_opening
    from skimage.util import img_as_ubyte, img_as_float
    DsRed_bin = DsRed > np.average(DsRed)
    GFP_th = img_as_float(percentile(GFP, img_as_ubyte(disk(20)), p0=0.75))
    GFP_bin = GFP > GFP_th
    # GFP_bin[binary_opening(GFP_bin)] = False
    DsRed[~DsRed_bin] = 0
    GFP[~GFP_bin] = 0
    # GFP = GFP_th
    return DsRed, GFP


@step
def binary_mask(DsRed, GFP):
    GFP[DsRed == 0] = 0
    return DsRed, GFP


@step
# @skip
def hough(DsRed, GFP):
    from skimage.transform import hough_circle
    DsRed = np.amax(hough_circle(DsRed, np.arange(8, 15)), axis=0) ** 2
    GFP = np.amax(hough_circle(GFP, np.arange(8, 15)), axis=0) ** 2
    return DsRed, GFP


@step
def grayscale_mask(DsRed, GFP):
    GFP = np.sqrt(GFP * DsRed)
    return DsRed, GFP


@step
def calc(DsRed, GFP):
    global stats, ratio, pixel_ratio
    ratio = np.sum(GFP.astype(np.float64)) / np.sum(DsRed.astype(np.float64))
    pixel_ratio = np.average(GFP.astype(np.float64))
    stats = GFP * 2 - DsRed
    stats[stats < 0] = 0
    stat_ratio = np.average(stats)
    print(f"Ratio: {round(ratio * 10000) / 100}%", file=sys.stderr)
    print(ratio)
    print(pixel_ratio)
    print(stat_ratio)
    stats = np.dstack([DsRed, GFP, stats])
    return DsRed, GFP


if interactive:
    from NanoImagingPack import view
    # view(stats)

    @step
    # @skip
    def blur(DsRed, GFP):
        from skimage.filters import gaussian
        sigma = 15
        DsRed = gaussian(DsRed, sigma)
        GFP = gaussian(GFP, sigma)
        return DsRed, GFP


    @step
    # @skip
    def visual_calc(DsRed, GFP):
        # ratio = np.divide(GFP, DsRed, where=DsRed != 0)
        ratio = GFP * 1.5 - DsRed
        ratio[ratio < 0] = 0
        print(f"Ratio: {round(np.average(ratio) * 10000) / 100}%", file=sys.stderr)
        # ratio = ratio * np.nanmedian(1 / ratio) / 2
        return ratio, ratio


    from NanoImagingPack import v5
    viewer = v5(np.array(img5), multicol=True)
    # note: using img4 instead of img5 is a good idea
    viewer.ProcessKeys('..T')

    @step
    def find_centers():
        from skimage.feature import peak_local_max
        import javabridge as jb
        my3DData = jb.get_field(viewer.o, 'data3d', 'Lview5d/My3DData;')
        myMarkerLists = jb.get_field(my3DData, 'MyMarkers', 'Lview5d/MarkerLists;')
        jb.set_field(my3DData, 'ConnectionShown', 'Z', False)

        def f(img, *kargs):
            coords = peak_local_max(img, min_distance=15, indices=True)
            result = []
            mask = np.ones_like(img) > 0
            while len(kargs) > 2:
                mask_img, th, invert_th = kargs[0:3]
                kargs = kargs[3:]

                from skimage.filters.rank import maximum
                from skimage.morphology import disk
                from skimage.util import img_as_ubyte, img_as_float
                # NanoImagingPack.view(mask_img)
                mask_img = np.minimum(np.maximum(mask_img,
                                                 np.zeros_like(stats[:,:,0])),
                                      np.ones_like(stats[:,:,0]))
                mask_img = img_as_float(maximum(img_as_ubyte(mask_img), disk(5)))
                bin = mask_img > th
                if invert_th:
                    bin = ~bin
                mask[~bin] = False

            for coord in coords:
                if mask[coord[0], coord[1]]:
                    for t in range(step_cnt):
                        result.append(np.array([t, 0, 0, coord[0], coord[1]]))
            return result

        viewer.setMarkers(f(stats[:,:,0], stats[:,:,0], 0.5, False, stats[:,:,1], 0.5, False), 1)
        viewer.setMarkers(f(stats[:,:,0], stats[:,:,0], 0.5, False, stats[:,:,1], 0.5, True), 2)
        jb.call(jb.call(myMarkerLists, 'GetMarkerList', '(I)Lview5d/MarkerList;', 1), 'SetColor', '(I)V', 0x00FF00)
        jb.call(jb.call(myMarkerLists, 'GetMarkerList', '(I)Lview5d/MarkerList;', 2), 'SetColor', '(I)V', 0x0000FF)
        return [stats]
    
    print("done")
else:
    from skimage.io import imsave
    from skimage.util import img_as_ubyte
    stats[stats > 1] = 1
    stats[stats < 0] = 0
    imsave(folder + '/stats.tif', img_as_ubyte(stats))
    # imsave(folder + '/composite.tif', composite)

