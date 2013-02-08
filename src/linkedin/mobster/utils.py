import commands
from datetime import datetime
import functools
from time import mktime, sleep, time

import pytz

def format_time(seconds):
  """
  Formats time in the following ISO-8601 format: YYYY-MM-DDThh:mm:ss.sTZD
  """
  dt = datetime.fromtimestamp(seconds, pytz.utc)
  formatted_dt = dt.strftime("%Y-%m-%dT%H:%M:%S.%f%z")

  # return the formatted string with a semicolon between the hour and minute offset components (per HAR file standard)
  return ":".join([formatted_dt[:-2], formatted_dt[-2:]])

def datetime_to_millis(dt):
  return mktime(dt.timetuple()) * 1e3 + dt.microsecond / 1e3

def wait_until(cond_func, timeout=120):
  """Wait until the specified function (with no args) returns true"""
  start_time = time()
  while not cond_func():
    if time() - start_time > timeout:
      raise Exception("wait_until timeout of {0}s reached".format(timeout))
    sleep(0.1)

def cmd_exists(cmd):
  """Returns true if the specified command is available in the PATH"""
  (status, output) = commands.getstatusoutput("which {0}".format(cmd))
  return status == 0

class memoize(object):
  """
  Memoize decorator.
  """
  def __init__(self, func):
    self.func = func
    self.memoized = {}
    self.method_cache = {}
  def __call__(self, *args):
    return self.cache_get(self.memoized, args,
      lambda: self.func(*args))
  def __get__(self, obj, objtype):
    return self.cache_get(self.method_cache, obj,
      lambda: self.__class__(functools.partial(self.func, obj)))
  def cache_get(self, cache, key, func):
    try:
      return cache[key]
    except KeyError:
      cache[key] = func()
      return cache[key]

def running_avg():
  """
  Generator and coroutine for keeping track of a changing average. Example usage:
  > avg_helper = running_avg()
  > avg_helper.next()
  > print avg_helper.send(1.0)
  1.0
  > avg_helper.next()
  > print avg_helper.send(2.0)
  1.5
  """

  count = 0
  total = 0.0

  while True:
    total += (yield)
    count += 1
    yield total/count
