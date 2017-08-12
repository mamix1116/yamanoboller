# -*- coding: utf-8 -*-

import re
import time
from datetime import datetime


def dt2ts(dt):
    return int(time.mktime(dt.timetuple()) * 1000) + (dt.microsecond // 1000)


def ts2dt(ts):
    return datetime.fromtimestamp(
        int(ts) // 1000
    ).replace(microsecond=(int(ts) % 1000 * 1000))


def trycast(t, d, e):
    try:
        return t(d)
    except Exception as expt:
        return e


def is_numeric(x):
    return re.match(
        r'^\s*[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?\s*$', x
    ) is not None
