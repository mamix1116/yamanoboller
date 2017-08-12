# -*- coding: utf-8 -*-

import numpy as np
from scipy.interpolate import interp1d


class YamapInterpolator(object):
    def __init__(self, data, **kwargs):
        super(YamapInterpolator, self).__init__()
        self.data = sorted(data, key=lambda x: x[0])
        self.x = np.array(list(map(lambda x: x[0], self.data)), dtype=np.float)
        self.y = np.array(
            list(map(lambda x: [x[1], x[2], x[3]], self.data)),
            dtype=np.float
        )
        ops = dict(dict({'kind': 'slinear'}, **kwargs), **{'axis': 0})
        self.ip = interp1d(x=self.x, y=self.y, **ops)

    @property
    def domain(self):
        return [np.min(self.x), np.max(self.x)]

    @property
    def lat_range(self):
        return [np.min(self.y[:, 0]), np.max(self.y[:, 0])]

    @property
    def lon_range(self):
        return [np.min(self.y[:, 1]), np.max(self.y[:, 1])]

    @property
    def alt_range(self):
        return [np.min(self.y[:, 2]), np.max(self.y[:, 2])]

    def __call__(self, t):
        return self.ip(t)


class FitbitInterpolator(object):
    def __init__(self, data, **kwargs):
        super(FitbitInterpolator, self).__init__()
        self.data = sorted(data, key=lambda x: x[0])
        self.x = np.array(list(map(lambda x: x[0], self.data)), dtype=np.float)
        self.y = np.array(list(map(lambda x: x[1], self.data)), dtype=np.float)
        ops = dict({'kind': 'slinear'}, **kwargs)
        self.ip = interp1d(x=self.x, y=self.y, **ops)

    @property
    def domain(self):
        return [np.min(self.x), np.max(self.x)]

    @property
    def range(self):
        return [np.min(self.y), np.max(self.y)]

    def __call__(self, t):
        return self.ip(t)
