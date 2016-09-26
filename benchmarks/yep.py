#!/usr/bin/env python
"""Yep Extension Profiler

Yep is a tool to profile compiled code (C/C++/Fortran) from the Python
interpreter. It uses the google-perftools CPU profiler and depends on
pprof for visualization.

See http://pypi.python.org/pypi/yep for more info.
"""

_CMD_USAGE = """usage: python -m yep [options] -- scriptfile [arg] ...

This will create a file scriptfile.prof that can be analyzed with
pprof (google-pprof on Debian-based systems).
"""
import sys
import ctypes.util

__version__ = '0.4'

#       .. find google-perftools ..
google_profiler = ctypes.util.find_library('profiler')
if google_profiler:
    libprofiler = ctypes.CDLL(google_profiler)
else:
    raise ImportError(
        'Unable to find libprofiler, please make sure google-perftools '
        'is installed on your system'
        )


def start(file_name=None):
    """
    Start the CPU profiler.

    Parameters
    ----------
    fname : string, optional
       Name of file to store profile count. If not given, 'out.prof'
       will be used
    """
    if sys.version_info >= (3, 0):
        if file_name is None:
            file_name = b'out.prof'
        status = libprofiler.ProfilerStart(bytes(file_name, 'ASCII'))
        if status < 0:
            raise ValueError('Profiler did not start')
    else:
        if file_name is None:
            file_name = 'out.prof'
        status = libprofiler.ProfilerStart(file_name)
        if status < 0:
            raise ValueError('Profiler did not start')


def stop():
    """Stop the CPU profiler"""
    libprofiler.ProfilerStop()


# ----------------------------------------------------------------------
def read_profile(file_name):
    """Read dump of profile file.

    The format is described in
    http://google-perftools.googlecode.com/svn/trunk/doc/cpuprofile-fileformat.html
    """
    import struct
    f = open(file_name, 'rb')

#   .. decide architecture  ..
    header_words = f.read(8)
    if header_words == chr(0) * 8:  # 64-bit
        word_size, word_type = 8, 'q'
        header_words = f.read(8)[:4]
    else:
        word_size, word_type = 4, 'i'


#   .. endianness ..
    if header_words[:-2] == 2 * chr(0):
        endian = '>'
    elif header_words[:-4:-2] == 2 * chr(0):
        endian = '<'
    else:
        raise ValueError('header size >= 2**16')

    header_words, = struct.unpack(endian + 'i', header_words[-4:])
    f.read(header_words * word_size)

#    .. records ..
    records = []
    while True:
        sample_count, n_pcs = struct.unpack(
            endian + 2 * word_type, f.read(2 * word_size))
        current_record = (sample_count, n_pcs, struct.unpack(
            endian + n_pcs * word_type, f.read(n_pcs * word_size)))
        if current_record == (0, 1, (0,)):
            break
        records.append(current_record)


#   .. mapped objects ..
    func_map = f.readlines()
    f.close()

    return records, func_map


def main():
    import sys, os, __main__
    from optparse import OptionParser
    parser = OptionParser(usage=_CMD_USAGE)
    parser.add_option('-o', '--outfile', dest='outfile',
        help='Save stats to <outfile>', default=None)
    parser.add_option('-v', '--visualize', action='store_true',
        dest='visualize', help='Visualize result at exit',
        default=False)
    parser.add_option('-c', '--callgrind', action='store_true',
        dest='callgrind', help='Output file in callgrind format',
        default=False)


    if not sys.argv[1:] or sys.argv[1] in ("--help", "-h"):
        parser.print_help()
        sys.exit(2)

    (options, args) = parser.parse_args()
    sys.argv[:] = args

#       .. get file name ..
    main_file = os.path.abspath(args[0])
    if options.outfile is None:
        options.outfile = os.path.basename(main_file) + '.prof'
    if not options.callgrind:
        out_file = options.outfile
    else:
        import tempfile
        tmp_file = tempfile.NamedTemporaryFile()
        out_file = tmp_file.name
    if not os.path.exists(main_file):
        print('Error:', main_file, 'does not exist')
        sys.exit(1)

#       .. execute file ..
    sys.path.insert(0, os.path.dirname(main_file))
    start(out_file)
    exec(compile(open(main_file).read(), main_file, 'exec'),
         __main__.__dict__)
    stop()

    if any((options.callgrind, options.visualize)):
        from subprocess import call
        try:
            res = call(['google-pprof', '--help'])
        except OSError:
            res = 1
        pprof_exec = ('google-pprof', 'pprof')[res != 0]

        if options.visualize:
#       .. strip memory address, 32 bit-compatile ..
            sed_filter = '/[[:xdigit:]]\{8\}$/d'
            call("%s --cum --text %s %s | sed '%s'" % \
                 (pprof_exec, sys.executable, options.outfile, sed_filter),
                 shell=True)

        if options.callgrind:
            call("%s --callgrind %s %s > %s" % \
                 (pprof_exec, sys.executable, out_file, options.outfile),
                 shell=True)
            tmp_file.close()


if __name__ == '__main__':
    main()
