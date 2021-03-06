#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import os
import shlex
import tempfile
from wdmtoolbox import wdmtoolbox

def _createwdm(fname):
    cmd = shlex.split('wdmtoolbox createnewwdm --overwrite {0}'.format(fname))
    return subprocess.call(cmd)

def test_createwdm():
    fd, fname = tempfile.mkstemp(suffix='.wdm')
    os.close(fd)
    assert _createwdm(fname) == 0
    wdmtoolbox.createnewwdm(fname, overwrite=True)
    # A brand spanking new wdm should be 40k
    assert os.path.getsize(fname) == 40*1024
    os.remove(fname)

def test_createnewdsn_checkdefaults():
    fd, fname = tempfile.mkstemp(suffix='.wdm')
    os.close(fd)
    assert _createwdm(fname) == 0
    cmd = shlex.split('wdmtoolbox createnewdsn {0} 101'.format(fname))
    retcode = subprocess.call(cmd)
    assert retcode == 0
    tstr = ['#DSN  SCENARIO LOCATION CONSTITUENT START DATE          END DATE            TCODE TSTEP',
            '  101                               None                None                    D(4) 1',
            '']
    tstr = '\n'.join(tstr)
    cmd = shlex.split('wdmtoolbox listdsns {0}'.format(fname))
    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         universal_newlines=True)

    astr, _ = p.communicate()
    assert p.returncode == 0

    assert astr == tstr

    os.remove(fname)

try:
    from cStringIO import StringIO
except:
    from io import StringIO

from pandas.util.testing import TestCase
from pandas.util.testing import assertRaisesRegexp

from wdmtoolbox import wdmtoolbox
from wdmtoolbox.wdmutil import WDMFileExists


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

    def test_overwrite(self):
        wdmtoolbox.createnewwdm(self.wdmname, overwrite=True)
        with assertRaisesRegexp(WDMFileExists, 'exists.'):
            wdmtoolbox.createnewwdm(self.wdmname)

