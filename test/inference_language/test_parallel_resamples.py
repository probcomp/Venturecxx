from nose.tools import eq_
import threading

from venture.test.config import get_ripl

def testSynchronousIsSerial():
  yield checkSynchronousIsSerial, "resample"
  yield checkSynchronousIsSerial, "resample_serializing"

def checkSynchronousIsSerial(mode):
  eq_(1, threading.active_count())
  r = get_ripl()
  eq_(1, threading.active_count())
  r.infer("(%s 2)" % mode)
  eq_(1, threading.active_count())
