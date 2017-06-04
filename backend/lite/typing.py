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

# This is a magic constant that mypy sets to true during type
# checking, as described under
# http://mypy.readthedocs.io/en/latest/common_issues.html#import-cycles
MYPY = False

try:
    # If typing is available, use it.  It's harmless in running code,
    # and some uses can be fairly sophisticated.
    from typing import *
except ImportError:
    if MYPY:
        # We are type-checking without the typing module: fail.
        raise
    else:
        # The typing module is not available, but we are not
        # typechecking: Try to stub the names.  Sufficiently simple
        # uses (such as occur in the code of Venture proper) should
        # execute.
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
