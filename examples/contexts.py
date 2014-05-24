import os
import time


class Timer(object):
    def __init__(self, task='task'):
        self.task = task
        self.start, self.stop, self.elapsed = None, None, None
        return
    def __str__(self):
        self_str = '%s took %.1f seconds' % (self.task, self.elapsed)
        return self_str
    def __enter__(self):
        self.start = time.time()
        return self
    def __exit__(self, *args):
        self.stop = time.time()
        self.elapsed = self.stop - self.start
        print self
        return
    pass


# http://stackoverflow.com/a/938800
scale_str_lookup = dict(kb=1024.0,mb=1024.0*1024.0)
key_lookup = dict(memory='VmSize:', resident='VmRSS:', stacksize='VmStk:')
#
def read_proc_status(pid=None):
    pid = os.getpid() if pid is None else pid
    pseudofile = '/proc/%d/status' % pid
    status_str = ''
    with open(pseudofile) as fh:
        status_str = fh.read()
        pass
    return status_str
def parse_proc_status(status_str, which_usage):
    usage_start = status_str.index(key_lookup[which_usage])
    return status_str[usage_start:].split(None, 3)
def process_parsed_proc_status(parsed):
    return float(parsed[1]) * scale_str_lookup[parsed[2].lower()]
def get_usage(which_usage='memory', since=0.0):
    status_str = read_proc_status()
    parsed = parse_proc_status(status_str, which_usage)
    return process_parsed_proc_status(parsed) - since
#
def get_short_size(size):
    size = int(size)
    gb = size / 2 ** 30
    if gb > 0:
        return '%sGB' % gb
    mb = size / 2 ** 20
    if mb > 0:
        return '%sMB' % mb
    kb = size / 2 ** 10
    if kb > 0:
        return '%sKB' % kb
    return '%s B' % size
class MemoryContext(object):
    def __init__(self, task='task', which_usage='memory'):
        self.task = task
        self.which_usage = which_usage
        self.start_usage, self.stop_usage, self.delta = None, None, None
        return
    def __str__(self):
        short_size = get_short_size(self.delta)
        self_str = '%s used %s (which_usage=%s)'
        self_str %= (self.task, short_size, self.which_usage)
        return self_str
    def get_usage(self):
        return get_usage(self.which_usage)
    def __enter__(self):
        self.start_usage = self.get_usage()
        return self
    def __exit__(self, *args):
        self.stop_usage = self.get_usage()
        self.delta = self.stop_usage - self.start_usage
        print self
        return
    pass
