import sys

import numpy as np
import NanoImagingPack as nip, bioformats

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} zvi_file")
    path = "mCD8-GFP_GlueRed_-6h-0023.zvi"
else:
    path = sys.argv[1]

reader = bioformats.get_image_reader(42, path=path)
planes = [[] for c in range(reader.rdr.getSizeC())]
for z in range(reader.rdr.getSizeZ()):
    img = reader.read(z=z)
    for c in range(reader.rdr.getSizeC()):
        planes[c].append(img[:,:,c])
img5 = np.array(planes)

nip.v5(img5)
