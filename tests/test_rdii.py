#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_rdii.py
----------------------------------

Tests for `wdmtoolbox` module.
"""

import sys
import os
import tempfile
try:
    from cStringIO import StringIO
except:
    from io import StringIO

from pandas.util.testing import TestCase

from wdmtoolbox import wdmtoolbox


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

    def test_rdii(self):
        wdmtoolbox.createnewwdm(self.wdmname, overwrite=True)
        wdmtoolbox.createnewdsn(self.wdmname, 101, tcode=2,
                                base_year=1970, tsstep=15)
        wdmtoolbox.csvtowdm(self.wdmname, 101,
                            input_ts='tests/nwisiv_02246000.csv')
        wdmtoolbox.copydsn(self.wdmname, 101, self.wdmname, 1101)
        wdmtoolbox.wdmtoswmm5rdii(self.wdmname, 101, 1101)


