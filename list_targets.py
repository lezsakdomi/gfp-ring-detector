import json
import os
import re

import toml


default_dataset = 'képek'


folder_re = re.compile('^(?P<name>.*)\.(?:zvi|tif)_[fF]iles$')
stat_line_re = re.compile('^(?P<feature>[^:]+): (?P<value>.*)\n?$')


class TargetFormatError(Exception):
    pass


class Target:
    def __init__(self, path, name=None, dataset=None):
        self.path = path
        if name is not None:
            self.name = name
        else:
            folder_re_match = folder_re.match(os.path.basename(path))
            if folder_re_match is None:
                raise TargetFormatError("Folder name is bad")
            self.name = folder_re_match.group('name')
        for c in range(3):
            if not os.path.exists(self.fname(c)):
                raise TargetFormatError(f"Image file for channel {c} not found")
        if os.path.isfile(self.stats_path):
            self.stats = {}
            with open(self.stats_path) as f:
                for line in f.readlines():
                    if not line:
                        continue
                    stat_line_re_match = stat_line_re.match(line)
                    if stat_line_re_match is None:
                        raise TargetFormatError("A stat line is invalid")
                    k = stat_line_re_match.group('feature')
                    k = k[0].lower() + k[1:]
                    v = stat_line_re_match.group('value')
                    self.stats[k] = v
        else:
            self.stats = None
        self.dataset = dataset or self.path
        while True:
            if os.path.exists(os.path.join(self.dataset, 'dataset.toml')):
                self.dataset_options = toml.load(os.path.join(self.dataset, 'dataset.toml'))
                break
            elif os.path.dirname(self.dataset) == self.dataset:  # already in root
                raise TargetFormatError("No dataset.toml")
            else:
                self.dataset = os.path.dirname(self.dataset)
        if dataset is not None:
            self.dataset = dataset

    def __str__(self):
        return f"Image {self.name} ({self.path})"

    @property
    def stats_path(self):
        return os.path.join(self.path, 'stats.txt')

    def save_stats(self):
        if self.stats is None:
            raise Exception("Image has no stats to save")

        with open(self.stats_path, 'w') as f:
            for k, v in self.stats.items():
                f.write(f"{k[0].upper()}{k[1:]}: {v}\n")

    @property
    def fname_template(self):
        return os.path.join(self.path, f"{self.name}_c{'{}'}.tif")

    def fname(self, c):
        return self.fname_template.format(c)

    def chread(self, c):
        import numpy as np
        from skimage.io import imread
        img = imread(self.fname(c))
        if len(img.shape) == 3 and img.shape[0] == 2 \
                and np.sum(np.abs(img[1, :, :] - img[0, :, :])) == 0:
            img = img[0, :, :]
        elif len(img.shape) == 3 and img.shape[2] == 3 \
                and np.sum(np.abs(img[:, :, 1] - img[:, :, 0])) == 0 \
                and np.sum(np.abs(img[:, :, 1] - img[:, :, 2])) == 0:
            img = img[:, :, 0]
        return img

    @property
    def csv_path(self):
        return os.path.splitext(self.stats_path)[0] + '.csv'


class SliceTarget(Target):
    def __init__(self, path, z=0, dataset=None):
        self.z = z
        super().__init__(path, dataset=dataset)

    def __str__(self):
        return f"Image {self.name}#{self.z} ({self.path}, z={self.z})"

    @property
    def stats_path(self):
        return os.path.join(self.path, f'stats_z{self.z}.txt')

    @property
    def fname_template(self):
        return os.path.join(self.path, f"{self.name}_z{self.z}c{'{}'}.tif")


class M2Target(Target):
    def __init__(self, path, dataset=None):
        super().__init__(path, dataset=dataset)

    def __str__(self):
        return f"M2 image {self.name} ({self.path})"

    @property
    def fname_template(self):
        return os.path.join(self.path, f"{self.name}_h0b0c{'{}'}x0-2048y0-2048.tif")


class CustomTarget(Target):
    def __init__(self, fname_template=None, folder=None):
        self._fname_template = fname_template
        super().__init__(os.path.dirname(fname_template) if folder is None else folder)

    @property
    def fname_template(self):
        if self._fname_template is not None:
            return self._fname_template
        else:
            return super().fname_template


def walk(dataset=None):
    if dataset is None:
        dataset = default_dataset

    if isinstance(dataset, list):
        for dataset in dataset:
            for target in walk(dataset):
                yield target

    for path, dirs, files in os.walk(dataset):
        try:
            yield Target(path, dataset=dataset)
        except TargetFormatError:
            try:
                yield M2Target(path, dataset=dataset)
            except TargetFormatError:
                i = 0
                while True:
                    try:
                        yield SliceTarget(path, i, dataset=dataset)
                        i += 1
                    except TargetFormatError:
                        break
