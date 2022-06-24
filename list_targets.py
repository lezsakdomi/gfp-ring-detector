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


def walk(dataset=None):
    if dataset is None:
        dataset = default_dataset

    for path, dirs, files in os.walk(dataset):
        try:
            yield Target(path)
        except TargetFormatError:
            pass


if __name__ == '__main__':
    import pandas as pd
    import numpy as np

    df = pd.DataFrame(columns=['name', 'h',
                               'fname_template',
                               'scalar ratio', 'scalar positives', 'stat',
                               'count', 'hit count', 'miss count', 'ratio',
                               ])

    h_re = re.compile('képek/(-?\d+)h/')

    for target in walk():
        print(target)
        row = {'name': target.name}
        h_re_match = h_re.match(target.path)
        if h_re_match:
            row['h'] = h_re_match.group(1)
        if target.stats:
            for k in target.stats:
                print(k, repr(target.stats[k]))
                row[k] = target.stats[k]
        df.loc[target.path] = row
    df = df.astype({
        'h': 'int',
        'scalar ratio': 'float',
        'scalar positives': 'float',
        'stat': 'float',
        'count': 'int',
        'hit count': 'int',
        'miss count': 'int',
        'ratio': 'float',
    })
    df['total count'] = df['hit count'] + df['miss count']
    print(df)

    import matplotlib.pyplot as plt
    # plt.figure()
    # df.hist(by='h', column='ratio')
    # plt.show()
    #
    # # fig, ax = plt.figure()
    # # df2 = pd.DataFrame(data=[[ for row in df['count']]], columns=['-2', '-6'], index=df['count'])
    # # df['-2'] = np.nan
    # # df['-6'] = np.nan
    # x = 'count'
    # y = 'hit count'
    # # x = 'scalar ratio'
    # # y = 'scalar positives'
    # df.loc[df['h'] == -2, '-2'] = df[df['h'] == -2][y]
    # df.loc[df['h'] == -6, '-6'] = df[df['h'] == -6][y]
    #
    # # df.plot(kind='scatter', x=x, y=y)
    # # plt.show()
    #
    # ax = df.plot(kind='scatter', x=x, y='-2', c='blue')
    # df.plot(ax=ax, kind='scatter', x=x, y='-6', c='red')
    # plt.show()

    h_list = [-2, -6]
    plt.boxplot([df[df['h'] == h]['ratio'] for h in h_list])
    plt.xticks(list(range(1, len(h_list) + 1)), [f'{h}h' for h in h_list])
    plt.show()

    x = 'total count'
    y = 'ratio'
    for h in h_list:
        plt.scatter(x=df[df['h'] == h][x], y=df[df['h'] == h][y], label=f'{h}h')
    plt.xlabel(x)
    plt.ylabel(y)
    plt.legend()
    plt.show()
