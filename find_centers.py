import os
import sys

import numpy as np
import NanoImagingPack as nip, bioformats
from scipy import ndimage as ndi
from skimage import io

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} mCD8-GFP_GlueRed_-6h-0023.zvi")

    reader = bioformats.get_image_reader(42, path="mCD8-GFP_GlueRed_-6h-0023.zvi")
else:
    reader = bioformats.get_image_reader(42, path=sys.argv[1])

img = reader.read(z=3)
gfp = img[:, :, 1]
kernels = []
corr = []
corr_max = []
planes = [[] for c in range(img.shape[2])]
min_z = 5
max_z = 25
print("Finding potential centers")
for z in range(min_z, max_z):
    if z == 0:
        corr.append(np.zeros(gfp.shape, dtype=np.float64))
    else:
        shape = (2 * z + 1, 2 * z + 1)
        x = np.linspace(-z, +z, shape[0])
        y = np.linspace(-z, +z, shape[1])
        x, y = np.meshgrid(x, y)
        kernel = np.zeros(shape)
        kernel[True] = 0
        kernel[x ** 2 + y ** 2 < (z + 1) ** 2] = -0.25
        kernel[x ** 2 + y ** 2 < z ** 2] = 1
        kernel[x ** 2 + y ** 2 < (z - z / 3) ** 2] = -1
        kernel = kernel / np.linalg.norm(kernel)
        nip.view(kernel)
        corred = ndi.correlate(gfp, kernel)
        corr.append(corred)
        if len(corr_max) > 0 and z >= min_z:
            corr_max.append(np.maximum(corr_max[-1], corr[-1]))
        else:  # corr_max is empty
            corr_max.append(corr[-1])
    for c in range(len(planes)):
        planes[c].append(img[:, :, c])
    pct = (z + 1) ** 2 / max_z ** 2  # coarse approximation
    print(f"{pct:.0%} ({z + 1}/{max_z})", end='\r')
planes.append(corr)
planes.append(corr_max)

pixelsize = [None, 1.0,
             reader.rdr.getMetadataValue('Scale Factor for Y'),
             reader.rdr.getMetadataValue('Scale Factor for X'),
             ]
# pixelsize = [None, 1.0,
#              1.0, 1.0,
#              ]
img5 = nip.image(np.array(planes), colormodel=None, unit=['px', 'µm', 'µm'])
img5.name = reader.path
plane_descriptions = [reader.rdr.getMetadataValue(f"Channel Name {c}") for c in range(len(planes))]
# plane_descriptions = ["dsRed", "GFP"]
img5.dim_description = plane_descriptions + [
    "Suspected centers with given diameter", "Max center so far"]

viewer = nip.v5(img5)
