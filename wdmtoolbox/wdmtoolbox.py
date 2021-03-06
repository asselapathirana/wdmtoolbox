#!/usr/bin/env python
"""The component functions of the wdmtoolbox.

Used to manipulate Watershed Data Management files for time-series.
"""
from __future__ import print_function

# Python batteries included imports
import os
import sys
import datetime

# Third party imports
import mando
from dateutil.parser import parse as dateparser

# Local imports
# Load in WDM subroutines
from . import wdmutil
from tstoolbox import tsutils

WDM = wdmutil.WDM()


def _describedsn(wdmpath, dsn):
    """Private function used by routines that need a description of DSN."""
    return WDM.describe_dsn(wdmpath, int(dsn))


def _copy_dsn(inwdmpath, indsn, outwdmpath, outdsn):
    """The local underlying function to copy a DSN."""
    WDM.copydsnlabel(inwdmpath, indsn, outwdmpath, outdsn)
    nts = WDM.read_dsn(inwdmpath, indsn)
    WDM.write_dsn(outwdmpath, int(outdsn), nts)


@mando.command
def copydsn(inwdmpath, indsn, outwdmpath, outdsn):
    """Make a copy of a DSN.

    :param inwdmpath: Path to input WDM file.
    :param indsn: Source DSN.
    :param outwdmpath: Path to clean copy WDM file.
    :param outdsn: Target DSN.
    """
    if inwdmpath == outwdmpath:
        import tempfile
        tempdir = tempfile.mkdtemp()
        tmpwdmpath = os.path.join(tempdir, 'temp.wdm')
        createnewwdm(tmpwdmpath)
        _copy_dsn(inwdmpath, indsn, tmpwdmpath, outdsn)
        _copy_dsn(tmpwdmpath, outdsn, outwdmpath, outdsn)
        os.remove(tmpwdmpath)
        os.removedirs(tempdir)
    else:
        _copy_dsn(inwdmpath, indsn, outwdmpath, outdsn)


@mando.command
def cleancopywdm(inwdmpath, outwdmpath, overwrite=False):
    """Make a clean copy of a WDM file.

    :param inwdmpath: Path to input WDM file.
    :param outwdmpath: Path to clean copy WDM file.
    :param overwrite: Whether to overwrite an existing outwdmpath.
    """
    if inwdmpath == outwdmpath:
        raise ValueError("""
*
*   The "inwdmpath" cannot be the same as "outwdmpath".
*
""")
    createnewwdm(outwdmpath, overwrite=overwrite)
    activedsn = []
    for i in range(1, 32000):
        try:
            activedsn.append(_describedsn(inwdmpath, i)['dsn'])
        except wdmutil.WDMError:
            continue
    # Copy labels (which copies DSN metadata and data)
    for i in activedsn:
        try:
            _copy_dsn(inwdmpath, i, outwdmpath, i)
        except wdmutil.WDMError:
            pass


@mando.command
def renumberdsn(wdmpath, olddsn, newdsn):
    """Renumber olddsn to newdsn.

    :param wdmpath: Path and WDM filename.
    :param olddsn: Old DSN to renumber.
    :param newdsn: New DSN to change old DSN to.
    """
    WDM.renumber_dsn(wdmpath, olddsn, newdsn)


@mando.command
def deletedsn(wdmpath, dsn):
    """Delete DSN.

    :param wdmpath: Path and WDM filename.
    :param dsn: DSN to delete.
    """
    WDM.delete_dsn(wdmpath, dsn)


@mando.command
def wdmtoswmm5rdii(wdmpath, *dsns, **kwds):
    """Print out DSN data to the screen in SWMM5 RDII format.

    :param wdmpath: Path and WDM filename.
    :param dsns:     The Data Set Numbers in the WDM file.
    :param start_date: If not given defaults to start of data set.
    :param end_date:   If not given defaults to end of data set.
    """
    start_date = kwds.setdefault('start_date', None)
    end_date = kwds.setdefault('end_date', None)

    # Need to make sure that all DSNs are the same interval and all are
    # within start and end dates.
    collect_tcodes = {}
    collect_tsteps = {}
    collect_keys = []
    for dsn in dsns:
        dsn_desc = _describedsn(wdmpath, dsn)
        collect_tcodes[dsn_desc['tcode']] = 1
        collect_tsteps[dsn_desc['tstep']] = 1
        if start_date:
            assert dateparser(start_date) >= dateparser(dsn_desc['start_date'])
        if end_date:
            assert dateparser(end_date) <= dateparser(dsn_desc['end_date'])
        collect_keys.append((dsn_desc['dsn'], dsn_desc['location']))
    assert len(collect_tcodes) == 1
    assert len(collect_tsteps) == 1

    collect_tcodes = list(collect_tcodes.keys())[0]
    collect_tsteps = list(collect_tsteps.keys())[0]

    collected_start_dates = []
    collected_end_dates = []
    collected_ts = {}
    for dsn, location in collect_keys:
        tmp = WDM.read_dsn(wdmpath,
                           int(dsn),
                           start_date=start_date,
                           end_date=end_date)
        collected_start_dates.append(tmp.index[0])
        collected_end_dates.append(tmp.index[-1])
        collected_ts[(dsn, location)] = tmp.values

    maptcode = {
        1: 1,
        2: 60,
        3: 3600,
        4: 86400,
        }

    print('SWMM5')
    print('RDII dump of DSNS {0} from {1}'.format(dsns, wdmpath))
    print(maptcode[collect_tcodes]*collect_tsteps)
    print(1)
    print('FLOW CFS')
    print(len(dsns))
    for dsn, location in collect_keys:
        print(str(dsn) + '_' + location)
    print('Node Year Mon Day Hr Min Sec Flow')
    # Can pick any time series because they should all have the same interval
    # and start and end dates.
    for dex, date in enumerate(tmp.index):
        for dsn, location in collect_keys:
            print(
                '{0}_{1} {2} {3:02} {4:02} {5:02} {6:02} {7:02} {8}'.format(
                    dsn, location, date.year, date.month, date.day, date.hour,
                    date.minute, date.second,
                    collected_ts[(dsn, location)][dex]))


def extract(*wdmpath, **kwds):
    """Print out DSN data to the screen with ISO-8601 dates.

    This is the API version also used by 'extract_cli'
    """
    # Adapt to both forms of presenting wdm files and DSNs
    # Old form '... file.wdm 101 102 103 ...'
    # New form '... file.wdm,101 adifferentfile.wdm,101 ...
    try:
        start_date = kwds.pop('start_date')
    except KeyError:
        start_date = None
    try:
        end_date = kwds.pop('end_date')
    except KeyError:
        end_date = None
    if len(kwds) > 0:
        raise ValueError("""
*
*   The only allowed keywords are start_date and end_date.  You
*   have given {0}.
*
""".format(kwds))

    labels = []
    for lab in wdmpath:
        if ',' in str(lab):
            labels.append(lab.split(','))
        else:
            if lab == wdmpath[0]:
                continue
            labels.append([wdmpath[0], lab])

    for index, lab in enumerate(labels):
        wdmpath = lab[0]
        dsn = lab[1]
        nts = WDM.read_dsn(wdmpath,
                           int(dsn),
                           start_date=start_date,
                           end_date=end_date)
        if index == 0:
            result = nts
        else:
            try:
                result = result.join(nts, how='outer')
            except:
                raise ValueError("""
*
*   The column {0} is duplicated.  Dataset names must be unique.
*
""".format(nts.columns[0]))
    return tsutils.printiso(result)


@mando.command('extract')
def extract_cli(start_date=None, end_date=None, *wdmpath):
    """Print out DSN data to the screen with ISO-8601 dates.

    :param wdmpath: Path and WDM filename followed by space separated list of
                    DSNs. For example,

                        'file.wdm 234 345 456'.
                    OR

                    `wdmpath` can be space separated sets of 'wdmpath,dsn'.
                    For example,

                        'file.wdm,101 file2.wdm,104 file.wdm,227'
    :param start_date: If not given defaults to start of data set.
    :param end_date:   If not given defaults to end of data set.
    """
    return extract(*wdmpath, start_date=start_date, end_date=end_date)


@mando.command
def wdmtostd(wdmpath, *dsns, **kwds):  # start_date=None, end_date=None):
    """DEPRECATED: New scripts use 'extract'. Will be removed in the future."""
    return extract(wdmpath, *dsns, **kwds)


@mando.command
def describedsn(wdmpath, dsn):
    """Print out a description of a single DSN.

    :param wdmpath: Path and WDM filename.
    :param dsn:     The Data Set Number in the WDM file.
    """
    print(_describedsn(wdmpath, dsn))


@mando.command
def listdsns(wdmpath):
    """Print out a table describing all DSNs in the WDM.

    :param wdmpath: Path and WDM filename.
    """
    if not os.path.exists(wdmpath):
        raise ValueError("""
*
*   File {0} does not exist.
*
""".format(wdmpath))

    dsn_info = {}
    cli = tsutils.test_cli()
    if cli is True:
        print('#{0:<4} {1:>8} {2:>8} {3:>8} {4:<19} {5:<19} {6:>5} {7}'.format(
            'DSN', 'SCENARIO', 'LOCATION', 'CONSTITUENT', 'START DATE',
            'END DATE', 'TCODE', 'TSTEP'))
    for i in range(1, 32001):
        try:
            testv = _describedsn(wdmpath, i)
        except wdmutil.WDMError:
            continue
        if cli is True:
            print('{dsn:5} {scenario!s:8} {location!s:8} {constituent!s:8}    {start_date!s:19} {end_date!s:19} {tcode_name!s:>5}({tcode}) {tstep}'.format(**testv))
        else:
            dsn_info[testv['dsn']] = testv
    if cli is False:
        return dsn_info


@mando.command
def createnewwdm(wdmpath, overwrite=False):
    """Create a new WDM file, optional to overwrite.

    :param wdmpath: Path and WDM filename.
    :param overwrite: Defaults to not overwrite existing file.
    """
    WDM.create_new_wdm(wdmpath, overwrite=overwrite)


@mando.command
def createnewdsn(wdmpath, dsn, tstype='', base_year=1900, tcode=4, tsstep=1,
                 statid='', scenario='', location='', description='',
                 constituent='', tsfill=-999.0):
    """Create a new DSN.

    :param wdmpath: Path and WDM filename.
    :param dsn: The Data Set Number in the WDM file.  This number must be
                greater or equal to 1 and less than or equal to 32000.  HSPF
                can only use for input or output DSNs of 999 or less.
    :param tstype: Time series type.  Can be any 4 character string, but
                   if not specified defaults to first 4 characters of
                   'constituent'.  Must match what is used in HSPF UCI
                   file.
    :param base_year: Base year of time series, defaults to 1900.  The DSN will
                      not accept any time-stamps before this date.
    :param tcode: Time series code, (1=second, 2=minute, 3=hour, 4=day,
                  5=month, 6= year) defaults to 4 = daily.
    :param tsstep: Time series steps, defaults (and almost always is) 1.
    :param statid: The station name, defaults to ''.
    :param scenario: The name of the scenario, defaults to ''.  Can be
                     anything, but typically, 'OBSERVED' for calibration and
                     input time-series and 'SIMULATED' for HSPF results.
    :param location: The location, defaults to ''.
    :param description: Descriptive text, defaults to ''.
    :param constituent: The constituent that the time series represents,
                        defaults to ''.
    :param tsfill: The value used as placeholder for missing values.
    """
    if tstype == '' and len(constituent) > 0:
        tstype = constituent[:4]
    WDM.create_new_dsn(wdmpath, int(dsn), tstype=tstype, base_year=base_year,
                       tcode=tcode, tsstep=tsstep, statid=statid,
                       scenario=scenario, location=location,
                       description=description, constituent=constituent,
                       tsfill=tsfill)


@mando.command
def hydhrseqtowdm(wdmpath, dsn, input_ts=sys.stdin, start_century=1900):
    """Write HYDHR sequential file to a DSN.

    :param wdmpath: Path and WDM filename.
    :param dsn: The Data Set Number in the WDM file.
    :param input_ts: Input filename, defaults to standard input.
    :param start_century: Since 2 digit years are used, need century, defaults
                          to 1900.
    """
    import pandas as pd
    dsn = int(dsn)
    if isinstance(input_ts, str):
        input_ts = open(input_ts, 'r')
    dates = pd.np.array([])
    data = pd.np.array([])
    for line in input_ts:
        words = line[8:]
        words = words.split()
        year = int(words[0]) + start_century
        month = int(words[1])
        day = int(words[2])
        ampmflag = int(words[3])
        if int(words[0]) == 99 and month == 12 and day == 31 and ampmflag == 2:
            start_century = start_century + 100
        data = pd.np.append(data, [float(i) for i in words[4:16]])
        try:
            if ampmflag == 1:
                dates = pd.np.append(dates,
                                     [datetime.datetime(year, month, day, i)
                                      for i in range(0, 12)])
            if ampmflag == 2:
                dates = pd.np.append(dates,
                                     [datetime.datetime(year, month, day, i)
                                      for i in range(12, 24)])
        except ValueError:
            print(start_century, line)
    data = pd.DataFrame(data, index=dates)
    _writetodsn(wdmpath, dsn, data)


@mando.command
def stdtowdm(wdmpath, dsn, infile='-'):
    """DEPRECATED: Use 'csvtowdm'."""
    csvtowdm(wdmpath, dsn, input_ts=infile)


@mando.command
def csvtowdm(wdmpath, dsn, input=None, start_date=None,
             end_date=None, columns=None, input_ts='-'):
    """Write data from a CSV file to a DSN.

    File can have comma separated
    'year', 'month', 'day', 'hour', 'minute', 'second', 'value'
    OR
    'date/time string', 'value'

    :param wdmpath: Path and WDM filename.
    :param dsn: The Data Set Number in the WDM file.
    :param input: DEPRECATED - use input_ts instead.
    :param input_ts: Filename with data in 'ISOdate,value' format or '-' for
       stdin.
    :param start_date: The start_date of the series in ISOdatetime format, or
        'None' for beginning.
    :param end_date: The end_date of the series in ISOdatetime format, or
        'None' for end.
    :param columns: Columns to pick out of input.  Can use column names or
        column numbers.  If using numbers, column number 1 is the first column.
        To pick multiple columns; separate by commas with no spaces. As used in
        'pick' command.
    """
    if input is not None:
        raise ValueError("""
*
*   The '--input' option has been deprecated.  Please use '--input_ts'
*   instead.
*
""")
    tsd = tsutils.common_kwds(tsutils.read_iso_ts(input_ts),
                              start_date=start_date,
                              end_date=end_date,
                              pick=columns)

    if len(tsd.columns) > 1:
        raise ValueError("""
*
*   The input data set must contain only 1 time series.
*   You gave {0}.
*
""".format(len(tsd.columns)))

    _writetodsn(wdmpath, dsn, tsd)


def _writetodsn(wdmpath, dsn, data):
    """Local function to write Pandas data frame to DSN."""
    data = tsutils.asbestfreq(data)
    infer = data.index.freqstr
    pandacode = infer.lstrip('0123456789')
    tstep = infer[:infer.find(pandacode)]
    try:
        tstep = int(tstep)
    except ValueError:
        tstep = 1

    mapcode = {
        'A':     6,  # annual
        'A-DEC': 6,  # annual
        'AS':    6,  # annual start
        'M':     5,  # month
        'MS':    5,  # month start
        'D':     4,  # day
        'H':     3,  # hour
        'T':     2,  # minute
        'S':     1   # second
        }
    try:
        finterval = mapcode[pandacode]
    except:
        raise KeyError("""
*
*   wdmtoolbox only understands PANDAS time intervals of :
*   'A', 'AS', 'A-DEC' for annual,
*   'M', 'MS' for monthly,
*   'D', 'H', 'T', 'S' for day, hour, minute, and second.
*   wdmtoolbox thinks this series is {0}.
*
""".format(pandacode))

    # Convert string to int
    dsn = int(dsn)

    # Make sure that input data metadata matches target DSN
    desc_dsn = _describedsn(wdmpath, dsn)

    dsntcode = desc_dsn['tcode']
    if finterval != dsntcode:
        raise ValueError("""
*
*   The DSN has a frequency of {0}, but the data has a frequency of {1}.
*
""".format(dsntcode, finterval))

    dsntstep = desc_dsn['tstep']
    if dsntstep != tstep:
        raise ValueError("""
*
*   The DSN has a tstep of {0}, but the data has a tstep of {1}.
*
""".format(dsntstep, tstep))

    WDM.write_dsn(wdmpath, dsn, data)


def main():
    """Main function."""
    if not os.path.exists('debug_wdmtoolbox'):
        sys.tracebacklimit = 0
    mando.main()


if __name__ == '__main__':
    main()
