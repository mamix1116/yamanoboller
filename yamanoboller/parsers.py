# -*- coding: utf-8 -*-

import os
import collections
import json
from datetime import datetime
from abc import ABCMeta, abstractmethod
import xml.etree.ElementTree as ET
import csv
import zipfile

import pytz

from . import util


class BaseParser(metaclass=ABCMeta):
    def __init__(self, fields):
        super(BaseParser, self).__init__()
        self.__fields = fields

    @property
    def fields(self):
        return self.__fields

    @abstractmethod
    def __call__(self, s):
        pass


class YamapParser(BaseParser):
    """Yamap GPX 形式のデータをリスト形式に変換する
    """

    def __init__(self):
        super(YamapParser, self).__init__(
            ['timestamp', 'latitude', 'longitude', 'altitude']
        )
        self.ns = '{http://www.topografix.com/GPX/1/1}'

    def __call__(self, s):
        if isinstance(s, ET.Element):
            return [[
                util.dt2ts(
                    datetime.strptime(
                        x.find(self.ns + 'time').text,
                        '%Y-%m-%dT%H:%M:%SZ'
                    ).astimezone(pytz.timezone('Asia/Tokyo'))
                ),
                float(x.attrib['lat']),
                float(x.attrib['lon']),
                float(x.find(self.ns + 'ele').text)
            ] for x in s.iter(self.ns + 'trkpt')]
        if isinstance(s, ET.ElementTree):
            return self(s.getroot())
        if hasattr(s, 'read') and callable(s.read):
            return self(ET.parse(s))
        if os.path.exists(s):
            with open(s, mode='r', encoding='utf-8') as fin:
                return self(fin)
        return self(ET.fromstring(s))


class FitbitParser(BaseParser):
    """Fitbit のデータをリスト形式に変換する
    """

    def __init__(self):
        super(FitbitParser, self).__init__(['timestamp', 'value'])

    def __call__(self, s):
        """Fitbit API から得られる json データをリストに変換する

        :param s: ファイル名を表す文字列か、``read`` 関数を持ったfile-likeオブジェクトか\
        辞書形式のオブジェクト。
        """
        if isinstance(s, collections.Mapping):
            date = s['activities-heart'][0]['dateTime']
            return [[
                util.dt2ts(datetime.strptime(date + ' ' + d['time'],
                           '%Y-%m-%d %H:%M:%S')), d['value']
            ] for d in s['activities-heart-intraday']['dataset']]
        if hasattr(s, 'read') and callable(s.read):
            return self(json.load(s))
        if os.path.exists(s):
            with open(s, mode='r', encoding='utf-8') as fin:
                return self(fin)
        return self(json.loads(s))


class FggmlParser(BaseParser):
    class GridGenerator(collections.Iterable):
        def __init__(self, lc, uc, low, high, start, ord):
            super(FggmlParser.GridGenerator, self).__init__()
            self.xlen = high[0] - low[0] + 1
            self.ylen = high[1] - low[1] + 1
            self.start = start
            self.xdir = 1 if ord[0] == '+' else -1
            self.ydir = 1 if ord[2] == '+' else -1
            self.lat_extent = (lc[0], uc[0])
            self.lng_extent = (lc[1], uc[1])
            self.x_unit = self.xdir * \
                (self.lng_extent[1] - self.lng_extent[0]) / (self.xlen)
            self.y_unit = self.ydir * \
                (self.lat_extent[1] - self.lat_extent[0]) / (self.ylen)
            self.origin = (self.lng_extent[0 if self.xdir == 1 else 1],
                           self.lat_extent[0 if self.ydir == 1 else 1])

        def __call__(self, x, y):
            return (self.origin[0] + self.x_unit * x,
                    self.origin[1] + self.y_unit * y)

        def __iter__(self):
            x = self.start[0]
            y = self.start[1]
            for i in range(y, self.ylen):
                for j in range(x, self.xlen):
                    yield self(j, i)
                x = 0

    def __init__(self):
        super(FggmlParser, self).__init__(
            ['latitude', 'longitude', 'altitude', 'type']
        )

    def __call__(self, s):
        if isinstance(s, ET.Element):
            dem = s.find('{http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema}DEM')
            lc = tuple(float(d) for d in dem.find(
                './/{http://www.opengis.net/gml/3.2}lowerCorner'
            ).text.split(' '))
            uc = tuple(float(d) for d in dem.find(
                './/{http://www.opengis.net/gml/3.2}upperCorner'
            ).text.split(' '))
            low = tuple(int(d) for d in dem.find(
                './/{http://www.opengis.net/gml/3.2}low'
            ).text.split(' '))
            high = tuple(int(d) for d in dem.find(
                './/{http://www.opengis.net/gml/3.2}high'
            ).text.split(' '))
            start = tuple(int(d) for d in dem.find(
                './/{http://www.opengis.net/gml/3.2}startPoint'
            ).text.split(' '))
            order_symbol = dem.find(
                './/{http://www.opengis.net/gml/3.2}sequenceRule'
            ).attrib['order']
            tl = [d for d in csv.reader(dem.find(
                './/{http://www.opengis.net/gml/3.2}tupleList'
            ).text.split('\n')) if len(d) > 0]
            return [
                [y, x, float(a), t] for ((x, y), (t, a)) in zip(
                    self.GridGenerator(lc, uc, low, high, start, order_symbol),
                    tl
                )
            ]
        if isinstance(s, ET.ElementTree):
            return self(s.getroot())
        if hasattr(s, 'read') and callable(s.read):
            return self(ET.parse(s))
        if os.path.exists(s):
            if zipfile.is_zipfile(s):
                with zipfile.ZipFile(s) as z:
                    res = []
                    for zi in z.infolist():
                        try:
                            with z.open(zi) as fin:
                                res += self(fin)
                        except Exception as e:
                            pass
                    return res
            else:
                with open(s, mode='r', encoding='utf-8') as fin:
                    return self(fin)
        return self(ET.fromstring(s))
