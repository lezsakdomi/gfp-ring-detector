import numpy as np
cimport numpy as np
cimport cython

np.import_array()

@cython.boundscheck(False)
@cython.wraparound(False)
def multi_flood(np.ndarray[np.float_t, ndim=2] img,
                np.ndarray[np.int_t, ndim=2] origins,
                np.ndarray[np.uint8_t, ndim=2, cast=True] mask = None,
                int iterations = 16):
    cdef int w = img.shape[0]
    cdef int h = img.shape[1]
    cdef int n = origins.shape[0]
    cdef int x
    cdef int y
    cdef np.ndarray[np.int_t, ndim=2] labels = np.zeros([w, h], dtype=int)
    cdef np.ndarray[np.int_t, ndim=2] distances = np.zeros([w, h], dtype=int)
    cdef np.ndarray[np.int_t, ndim=2] counts = np.zeros([n, iterations], dtype=int)
    cdef int i
    for i in range(n):
        x = origins[i, 0]
        y = origins[i, 1]
        labels[x, y] = i
        distances[x, y] = 1
        counts[i, 0] = 1
    for i in range(2, iterations + 1):
        for x in range(2, w - 2):
            for y in range(2, h - 2):
                if mask is not None and not mask[x, y]:
                    continue
                elif labels[x, y] != 0:
                    continue
                else:
                    if distances[x-1, y-1] == i - 1:
                        if img[x-1, y-1] > img[x, y]:
                            labels[x, y] = labels[x-1, y-1]
                        else:
                            continue
                    elif distances[x, y-1] == i - 1:
                        if img[x, y-1] > img[x, y]:
                            labels[x, y] = labels[x, y-1]
                        else:
                            continue
                    elif distances[x, y-2] == i - 1:
                        if img[x, y-2] > img[x, y]:
                            labels[x, y] = labels[x, y-2]
                        else:
                            continue
                    elif distances[x+1, y-1] == i - 1:
                        if img[x+1, y-1] > img[x, y]:
                            labels[x, y] = labels[x+1, y-1]
                        else:
                            continue
                    elif distances[x+1, y] == i - 1:
                        if img[x+1, y] > img[x, y]:
                            labels[x, y] = labels[x+1, y]
                        else:
                            continue
                    elif distances[x+2, y] == i - 1:
                        if img[x+2, y] > img[x, y]:
                            labels[x, y] = labels[x+2, y]
                        else:
                            continue
                    elif distances[x + 1, y + 1] == i - 1:
                        if img[x + 1, y + 1] > img[x, y]:
                            labels[x, y] = labels[x + 1, y + 1]
                        else:
                            continue
                    elif distances[x, y + 1] == i - 1:
                        if img[x, y + 1] > img[x, y]:
                            labels[x, y] = labels[x, y + 1]
                        else:
                            continue
                    elif distances[x, y + 2] == i - 1:
                        if img[x, y + 2] > img[x, y]:
                            labels[x, y] = labels[x, y + 2]
                        else:
                            continue
                    elif distances[x-1, y+1] == i - 1:
                        if img[x-1, y+1] > img[x, y]:
                            labels[x, y] = labels[x-1, y+1]
                        else:
                            continue
                    elif distances[x-1, y] == i - 1:
                        if img[x-1, y] > img[x, y]:
                            labels[x, y] = labels[x-1, y]
                        else:
                            continue
                    elif distances[x-2, y] == i - 1:
                        if img[x-2, y] > img[x, y]:
                            labels[x, y] = labels[x-2, y]
                        else:
                            continue
                    else:
                        continue

                    distances[x, y] = i
                    counts[labels[x, y], i - 1] += 1
    return labels, distances, counts
