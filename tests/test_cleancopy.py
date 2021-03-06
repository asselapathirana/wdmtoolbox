#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_createnewdsn
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
from pandas.util.testing import assertRaisesRegexp

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

    def test_cleancopytoself(self):
        wdmtoolbox.createnewwdm(self.wdmname, overwrite=True)
        wdmtoolbox.createnewdsn(self.wdmname, 101, tcode=2,
                                base_year=1970, tsstep=15)
        wdmtoolbox.csvtowdm(self.wdmname, 101,
                            input_ts='tests/nwisiv_02246000.csv')
        with assertRaisesRegexp(ValueError,
            'The "inwdmpath" cannot be the same as "outwdmpath"'):
            wdmtoolbox.cleancopywdm(self.wdmname, self.wdmname)

    def test_cleancopy_a_to_b(self):
        wdmtoolbox.createnewwdm(self.wdmname, overwrite=True)
        wdmtoolbox.createnewdsn(self.wdmname, 101, tcode=2,
                                base_year=1970, tsstep=15)
        wdmtoolbox.csvtowdm(self.wdmname, 101,
                            input_ts='tests/nwisiv_02246000.csv')
        tfd, twdmname = tempfile.mkstemp(suffix='.wdm')
        os.close(tfd)
        wdmtoolbox.cleancopywdm(self.wdmname, twdmname, overwrite=True)
        os.remove(twdmname)

