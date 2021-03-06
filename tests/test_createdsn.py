#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_createnewdsn
----------------------------------

Tests for `tstoolbox` module.
"""

import sys
import os
import tempfile
try:
    from cStringIO import StringIO
except:
    from io import StringIO

from pandas.util.testing import TestCase
from pandas.util.testing import assert_frame_equal
from pandas.util.testing import assertRaisesRegexp

from tstoolbox import tstoolbox
from wdmtoolbox import wdmtoolbox
from wdmtoolbox.wdmutil import DSNExistsError


def capture(func, *args, **kwds):
    sys.stdout = StringIO()      # capture output
    out = func(*args, **kwds)
    out = sys.stdout.getvalue()  # release output
    try:
        out = bytes(out, 'utf-8')
    except:
        pass
    return out


class TestDescribe(TestCase):
    def setUp(self):
        self.fd, self.wdmname = tempfile.mkstemp(suffix='.wdm')
        os.close(self.fd)

    def tearDown(self):
        os.remove(self.wdmname)

    def test_extract(self):
        wdmtoolbox.createnewwdm(self.wdmname, overwrite=True)
        wdmtoolbox.createnewdsn(self.wdmname, 101, tcode=5,
                                base_year=1870)
        wdmtoolbox.csvtowdm(self.wdmname, 101,
                            input_ts='tests/sunspot_area.csv')
        ret1 = wdmtoolbox.extract(self.wdmname, 101)
        ret2 = wdmtoolbox.extract('{0},101'.format(self.wdmname))
        assert_frame_equal(ret1, ret2)

        ret3 = tstoolbox.read('tests/sunspot_area.csv')
        ret1.columns = ['Area']
        assert_frame_equal(ret1, ret3)

        ret4 = tstoolbox.read('tests/sunspot_area_with_missing.csv',
                              dropna='no')

        wdmtoolbox.createnewdsn(self.wdmname, 500, tcode=5,
                                base_year=1870)
        wdmtoolbox.csvtowdm(self.wdmname, 500,
                            input_ts='tests/sunspot_area_with_missing.csv')
        ret5 = wdmtoolbox.extract(self.wdmname, 500)
        ret5.columns = ['Area']
        assert_frame_equal(ret5, ret4)

    def test_dsn_exists(self):
        wdmtoolbox.createnewwdm(self.wdmname, overwrite=True)
        wdmtoolbox.createnewdsn(self.wdmname, 101, tcode=5,
                                base_year=1870)
        with assertRaisesRegexp(DSNExistsError, 'exists.'):
            wdmtoolbox.createnewdsn(self.wdmname, 101, tcode=5,
                                    base_year=1870)
