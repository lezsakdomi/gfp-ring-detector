import os
import re


default_dataset = 'képek'


folder_re = re.compile('^(?P<name>.*)\.tif_Files$')
stat_line_re = re.compile('^(?P<feature>[^:]+): (?P<value>.*)\n?$')


class TargetFormatError(Exception):
    pass


class Target:
    def __init__(self, path, name=None):
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
                    stat_line_re_match = stat_line_re.match(line)
                    if stat_line_re_match is None:
                        raise TargetFormatError("A stat line is invalid")
                    k = stat_line_re_match.group('feature')
                    k = k[0].lower() + k[1:]
                    v = stat_line_re_match.group('value')
                    self.stats[k] = v
        else:
            self.stats = None
        self.dataset = self.path
        while True:
            if os.path.exists(os.path.join(self.dataset, 'dataset.toml')):
                break
            elif os.path.dirname(self.dataset) == self.dataset:  # already in root
                raise TargetFormatError("No dataset.toml")
            else:
                self.dataset = os.path.dirname(self.dataset)

    def __str__(self):
        return f"Image {self.name} ({self.path})"

    @property
    def stats_path(self):
        return os.path.join(self.path, 'stats.txt')

    @property
    def fname_template(self):
        return os.path.join(self.path, f"{self.name}_c{'{}'}.tif")

    def fname(self, c):
        return self.fname_template.format(c)

    def chread(self, c):
        from skimage.io import imread
        img = imread(self.fname(c))
        return img


class SliceTarget(Target):
    def __init__(self, path, z=0):
        self.z = z
        super().__init__(path)

    def __str__(self):
        return f"Image {self.name}#{self.z} ({self.path}, z={self.z})"

    @property
    def stats_path(self):
        return os.path.join(self.path, f'stats_z{self.z}.txt')

    @property
    def fname_template(self):
        return os.path.join(self.path, f"{self.name}_z{self.z}c{'{}'}.tif")


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

    for path, dirs, files in os.walk(dataset):
        try:
            yield Target(path)
        except TargetFormatError:
            i = 0
            while True:
                try:
                    yield SliceTarget(path, i)
                    i += 1
                except TargetFormatError:
                    break


if __name__ == '__main__':
    import pandas as pd
    import numpy as np

    df = pd.DataFrame(columns=['name', 'h',
                               'count', 'positive', 'negative', 'invalid',
                               ])

    h_re = re.compile(r'.*_(-?\d+)h-\d{4}$')

    for target in walk():
        # print(target)
        row = {'name': target.name}
        h_re_match = h_re.match(target.name)
        if h_re_match:
            row['h'] = h_re_match.group(1)
        if target.stats:
            for k in target.stats:
                # print(k, repr(target.stats[k]))
                row[k] = target.stats[k]
        df.loc[target.path] = row
    df = df.astype({
        'h': 'Int64',
        'count': 'Int64',
        'positive': 'Int64',
        'negative': 'Int64',
        'invalid': 'Int64',
    })
    df['total'] = df['positive'] + df['negative']
    df['positive ratio'] = df['positive'] / df['total']
    print(df)
    print()
    print(df.describe())
    df.to_csv(os.path.join(default_dataset, 'stats.csv'), index_label="path")

    import matplotlib.pyplot as plt

    h_list = df[~df['positive ratio'].isna()]['h'].unique()
    fil_list = [df['h'].isna() if pd.isna(h) else df['h'] == h for h in h_list]
    lab_list = [str(h) if pd.isna(h) else f'{h}h' for h in h_list]
    plt.boxplot([df[fil * ~df['positive ratio'].isna()]['positive ratio'] for fil in fil_list])
    plt.xticks(list(range(1, len(lab_list) + 1)), lab_list)
    plt.savefig(os.path.join(default_dataset, 'stats.boxplot.png'))
    plt.show()

    x = 'total'
    y = 'positive ratio'
    for fil, lab in zip(fil_list, lab_list):
        fil = fil * ~df[x].isna() * ~df[y].isna()
        plt.scatter(x=df[fil][x], y=df[fil][y], label=lab)
    plt.xlabel(x)
    plt.ylabel(y)
    plt.legend()
    plt.savefig(os.path.join(default_dataset, 'stats.scatter.png'))
    plt.show()

    print()
