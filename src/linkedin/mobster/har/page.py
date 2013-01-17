import logging
import time
import sys

class PageEventHandler(object):
  def __init__(self):
    self.page_loaded = False

  def process_event(self, message):
    if message['method'] == 'Page.loadEventFired':
      logging.info('Page.loadEventFired recorded')
      self.page_loaded = True


class PageLoadNotifier(object):
  def __init__(self, wait_for_page_load_event, network_event_timeout=3):
    self._received_page_load_event = False
    self._network_event_timeout = network_event_timeout
    self._wait_for_page_load_event = wait_for_page_load_event

    # set the last network event time to be super large initially, since it needs to not be considerably smaller
    # than the current time, or we will prematurely report a page load
    self._last_network_event_time = sys.maxint

  def process_timeline_event(self, message):
    pass

  def process_page_event(self, message):
    if message['method'] == 'Page.loadEventFired':
      logging.info('Page.loadEventFired recorded')
      self._received_page_load_event = True


  def process_network_event(self, message):
    self._last_network_event_time = time.time()

  def page_loaded(self):
    """
    Returns true if we have decided that the page is "loaded", false otherwise. If wait_for_page_load_event is true,
    the page is "loaded" when we
    """
    curr_time = time.time()
    if curr_time - self._last_network_event_time > self._network_event_timeout:
      if not self._wait_for_page_load_event or self._received_page_load_event:
        return True

    return False
