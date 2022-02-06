import os
from time import sleep, perf_counter
import numpy as np
from NanoImagingPack import image, v5, vv
from skimage import io, transform, exposure, filters

target = io.imread('steps.jpg', as_gray=True).astype("float")
target = target[183:1223, 201:1578]
target = transform.resize(target, (1040, 1388), anti_aliasing=True)
# target = target / np.linalg.norm(target)
# target = exposure.equalize_hist(target)
target = filters.gaussian(target, 3)

cnt = 0
last_time = perf_counter()
last_cnt = cnt
for root, dirs, files in os.walk("kepek"):
    for file in files:
        if file.endswith("_c0.tif"):
            cnt += 1
            filename = os.path.join(root, file)
            hit = io.imread(filename, as_gray=True).astype("float")
            # img = img / np.linalg.norm(img)
            hit = filters.gaussian(hit, 3)
            hit = exposure.match_histograms(hit, target)
            try:
                diff_img = target - hit
                diff = np.average(diff_img ** 2)
                th = 0.01
                if diff < th or perf_counter() - last_time > 60:
                    print(diff, cnt, (last_time - perf_counter()) / (last_cnt - cnt), file)
                    last_time = perf_counter()
                    last_cnt = cnt
                if diff < th:
                    hit = image(np.array([[diff_img], [target], [hit]]), name=file, info=filename)
                    hit.dim_description = ["Difference", "Target", "Hit"]
                    v5(hit)
                    # sleep(10)
            except Exception:
                pass
