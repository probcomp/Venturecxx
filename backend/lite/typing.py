# A centralized place whence to play necessary games to avoid a hard
# dependency on the standard typing module.
#
# Why is it feasible to avoid that dependency?  Because that module is
# only needed for typechecking, which not all users will want to do.
#
# Why is it desirable to avoid that dependency?  Because the 2.7
# backport of that module does not appear to be packaged even in
# Ubuntu 16.04.

from __future__ import absolute_import

# Conditionalize trying to import the typing module on whether or not
# we are typechecking with mypy, as recommended under
# http://mypy.readthedocs.io/en/latest/common_issues.html#import-cycles
MYPY = False
if MYPY:
    from typing import *
else:
    class bogus_container(object):
        def __getitem__(self, *args, **kwargs): return object
    Any = None
    Callable = bogus_container()
    Dict = bogus_container()
    Generic = bogus_container()
    List = bogus_container()
    Type = None
    Tuple = bogus_container()
    Union = bogus_container()
    TYPE_CHECKING = False
    def TypeVar(*args, **kwargs): return None
