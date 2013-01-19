import json

from linkedin.mobster.har.css import CSSProfileParser
from linkedin.mobster.har.network import NetworkEventHandler
from linkedin.mobster.har.page import PageEventHandler, PageLoadNotifier
from linkedin.mobster.har.timeline import TimelineEventHandler
from linkedin.mobster.utils import wait_until, format_time
from linkedin.mobster.webkitclient import RemoteWebKitClient
from linkedin.mobster.webkitcommunicator import RemoteWebKitCommunicator

class FlowProfiler(RemoteWebKitClient):
  """
  Runs a flow and records profiling information for each navigation. Generates HAR file.
  """
  def __init__(self, test_file, iterations=1):
    super(FlowProfiler, self).__init__(RemoteWebKitCommunicator())
    assert iterations > 0, "iterations must be a positive integer"
    self._iterations = iterations
    self._page_event_handler = None
    self._network_event_handler = None
    self._timeline_event_handler = None
    self._css_profiler_handler = None


    with open(test_file, 'r') as f:
      self._test = json.loads(f.read())

    assert len(self._test) > 0, 'The test must have at least one navigation'


  def profile(self):
    """
    Runs the test specified by the test file given to the constructor, and returns a list of HAR files (one for each
    navigation)
    """

    # list of list of har files: [[hars from run 1], [hars from run 2], ...]
    iteration_hars = []

    for x in range(0, self._iterations):
      hars = []
      self.clear_http_cache()
      self.clear_cookies()

      # Navigate to about:blank, to reset memory, etc.
      self._page_event_handler = PageEventHandler()
      self.start_page_event_monitoring(self._page_event_handler.process_event)
      self.navigate_to('about:blank')
      wait_until(lambda: self._page_event_handler.page_loaded)
      self.stop_page_event_monitoring()

      for navigation in self._test['navigations']:
        assert len(navigation) > 0, 'Each navigation must have at least one action'

        # do all the actions except the last one, because the last action causes the actual page navigation
        for i in range(0, len(navigation) - 1):
          self.process_action(navigation[i])

        self._network_event_handler = NetworkEventHandler()
        try:
          wait_for_page_load_event = navigation[-1]['wait-for-page-load']
        except KeyError:
          wait_for_page_load_event = True
        try:
          self._page_load_notifier = PageLoadNotifier(wait_for_page_load_event, navigation[-1]['network-timeout'])
        except KeyError:
          self._page_load_notifier = PageLoadNotifier(wait_for_page_load_event)

        self._timeline_event_handler = TimelineEventHandler()
        self.start_network_monitoring(self._network_event_handler.process_event)
        self.start_timeline_monitoring(self._timeline_event_handler.process_event)
        self.start_page_event_monitoring(self._page_load_notifier.process_page_event)
        self._communicator.add_domain_callback('Network', 'page_load_notifier', self._page_load_notifier.process_network_event)
        self._communicator.add_domain_callback('Timeline', 'page_load_notifier', self._page_load_notifier.process_timeline_event)
        self.start_css_selector_profiling()
        self.process_action(navigation[-1])

        wait_until(lambda: self._page_load_notifier.page_loaded())
        self.stop_page_event_monitoring()
        self.stop_timeline_monitoring()
        self.stop_network_monitoring()
        self._css_profiler_handler = CSSProfileParser(self.stop_css_selector_profiling())

        hars.append(self.make_har(navigation[-1]['page-name']))

      iteration_hars.append(hars)

    return iteration_hars


  def process_action(self, action):
    {
      'navigate': lambda: self.navigate_to(action['params']['url']),
      'textfield-set': lambda: self.set_field_value(action['params']['id'], action['params']['value']),
      'click': lambda: self.click_button(action['params']['id']),
      'dispatch-event': lambda: self.dispatch_event(action['params']),
      'form-submit': lambda: self.submit_form_by_id(action['params']['id']),
      'link-click': lambda: self.submit_form_by_id(action['params']),
      'raw-js': lambda: self.run_js(';'.join(action['params']['lines']))
    }[action['type']]()

  def make_har(self, page_name):
    """
    Returns a python dictionary which can be turned into a HAR file via conversion to JSON.

    page_name is this name that the flow file assigned to this page.
    """
    return {
      'log': {
        'version': '1.2',
        'creator': {
          'name': 'Mobster',
          'version': '1.0'
        },
        '_os': {
           '_name': self.get_os_name(),
           '_version': self.get_os_version()
        },
        'browser': {
          'name': self.get_browser_name(),
          'version': self.get_browser_version()
        },
        'pages': [self.make_page_info(page_name)],
        'entries': self._network_event_handler.make_entry_list()
      }
    }

  def make_page_info(self, page_name):
    """
    Make the 'page' entry for this page, which goes into the 'pages' section of the HAR file.
    Includes overall page timings and some memory-related information which is not included in
    normal HAR files
    """

    return {
      'startedDateTime': format_time(self._network_event_handler.get_first_request_time()),
      'id': self._network_event_handler.primary_page_id,
      'title': self.run_js('document.title'),
      '_pageName': page_name,
      'pageTimings': self.get_page_timings(),
      '_memoryStats': self._timeline_event_handler.get_memory_stats(),
      '_eventStats': self._timeline_event_handler.get_event_stats(),
      '_domNodeStats': self.get_dom_node_count(),
      '_cssStats': self._css_profiler_handler.get_css_stats()
    }


  def get_page_timings(self):
    """
    Returns a dictionary containing onContentLoad and onLoad times, both in (whole) milliseconds from
    the start of the request
    """
    browser_timings = self.get_window_performance()
    first_request_start = self._network_event_handler.get_first_request_time()
    return {
      'onContentLoad': max(int(browser_timings['domContentLoadedEventEnd'] - (first_request_start * 1000)), -1),
      'onLoad' : max(int(browser_timings['loadEventEnd'] - (first_request_start * 1000)), -1)
    }

