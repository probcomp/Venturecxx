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

from typing import *
