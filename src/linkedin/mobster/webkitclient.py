from pprint import pformat
import re
import logging

from linkedin.mobster.utils import memoize
from utils import wait_until

class RemoteWebKitClient(object):

  def __init__(self, communicator):
    self._communicator = communicator
    self._timeline_started = False
    self._network_enabled = False
    self._can_clear_cache = None
    self._has_heap_profiler = None
    self._heap_profiling_started = False
    self._profiling_enabled = False
    self._debugging_enabled = False
    self._page_events_enabled = False
    self._css_profiling_started = False
    self._css_profile = None


  def stop(self):
    """
    Releases websocket being used for debugging
    """
    self._communicator.stop()

  # --------------------------------------------------------------------------
  # RUNTIME
  # --------------------------------------------------------------------------

  def run_js(self, js, is_expression=True):
    """
    Runs JS in the current browser page, and returns the value if the JS is an expression.
    Otherwise, returns None.
    """
    self._got_js_result = False
    self._js_result = None

    def response_handler(response):
      if not is_expression:
        self._got_js_result = True
      elif 'result' in response and 'result' in response['result']:
        if 'wasThrown' in response['result']['result']:
          logging.error('Received error after running JS: {0}\n{1}'.format(js, response['result']))

        self._js_result = response['result']['result']['value']
        self._got_js_result = True

    self._communicator.send_cmd('Runtime.evaluate',
                                {'expression': js,
                                 'objectGroup': 'group',
                                 'returnByValue': True },
                                response_handler)
    self._communicator.send_cmd('Runtime.releaseObjectGroup',
                                {'objectGroup': 'group' },
                                response_handler)

    wait_until(lambda: self._got_js_result)
    return self._js_result

  def get_window_performance(self):
    """
    Returns an object containing an assortment of performance timings
    See: https://dvcs.w3.org/hg/webperf/raw-file/tip/specs/NavigationTiming/Overview.html#sec-navigation-timing-interface
    """
    return self.run_js('window.performance')['timing']

  # --------------------------------------------------------------------------
  # MEMORY
  # --------------------------------------------------------------------------

  def get_dom_node_count(self):
    """Returns an object containing groups of DOM nodes and their respective sizes"""
    self._dom_node_count = None

    def response_handler(response):
      self._dom_node_count = response['result']

    self._communicator.send_cmd('Memory.getDOMNodeCount', {}, response_handler)

    wait_until(lambda: self._dom_node_count)
    return self._dom_node_count

  def get_proc_memory_info(self):
    """
    Returns information about all the memory being used by the process (i.e. memory for DOM,
    JS, etc.)

    NOTE: Memory.getProcessMemoryDistribution was added to WebKit in May 2012. If the
    connected browser is a release from before then, this will NOT work. Tested to work
    in Chrome Canary as of 7-12-2012 (Chrome v.22).
    """

    logging.error('get_proc_memory_info: This function only works on the very latest browsers. Do not use.')

    self._memory_info = None

    def response_handler(response):
      try:
        self._memory_info = response['result']
      except KeyError, e:
        logging.error('Browser is too old to feature Memory.getProcessMemoryDistribution')

    self._communicator.send_cmd('Memory.getProcessMemoryDistribution', {}, response_handler)

    wait_until(lambda: self._memory_info)
    return self._memory_info



  # --------------------------------------------------------------------------
  # PROFILER
  # --------------------------------------------------------------------------

  @memoize
  def has_heap_profiler(self):
    def response_handler(response):
      self._has_heap_profiler = response['result']['result']

    self._communicator.send_cmd('Profiler.hasHeapProfiler', {}, response_handler)

    wait_until(lambda: self._has_heap_profiler != None)
    return self._has_heap_profiler

  def enable_profiling(self):
    """
    Generally enables profiling. Must be called before calling enable_heap_profiling(). Also required before doing CSS
    profiling, but CSS profiling has not been implemented for this client yet.
    """
    if self._profiling_enabled:
      logging.warning('Profiling already enabled')
      return

    def start_callback(m):
      self._profiling_enabled = True

    self._communicator.send_cmd('Profiler.enable', {})
    wait_until(lambda: self._profiling_enabled)

  def disable_profiling(self):
    if not self._profiling_enabled:
      logging.warning('Profiling already disabled')
      return

    def stop_callback(m):
      self._profiling_enabled = False

    self._communicator.send_cmd('Profiler.disable')
    wait_until(lambda: not self._profiling_enabled)

  def start_heap_profiling(self, callback):
    """
    Starts heap profiling, enabling heap snapshots
    """
    if not self.has_heap_profiler():
      logging.error('Browser cannot do heap profiling')
      return

    if self._heap_profiling_started:
      logging.warning('Heap profiling already started')
      return

    def profile_event_handler(response):
      if 'method' in response and response['method'].startswith('Profiler.'):
        callback(response)

    self._communicator.add_domain_callback('Profiler', 'profile_event', profile_event_handler)
    self._communicator.send_cmd('Profiler.start')
    self._heap_profiling_started = True


  def stop_heap_profiling(self):
    if not self._heap_profiling_started:
      logging.warning('Heap profile already started')
      return

    self._communicator.send_cmd('Profiler.stop')
    self._communicator.remove_domain_callback('Profiler', 'profile_event')
    self._heap_profiling_started = False

  def take_heap_snapshot(self):
    """Takes a heap snapshot, which can be retrieved using get_heap_profile()"""
    self._heap_snapshot_finished = False

    def progress_callback(response):
      if response['method'] == 'Profiler.reportHeapSnapshotProgress':
        self._heap_snapshot_finished = (response['params']['done'] == response['params']['total'])

    self._communicator.add_domain_callback('Profiler', 'heap_snapshot_progress', progress_callback)
    self._communicator.send_cmd('Profiler.takeHeapSnapshot')

    wait_until(lambda: self._heap_snapshot_finished)
    self._communicator.remove_domain_callback('Profiler', 'heap_snapshot_progress')


  def clear_profiles(self):
    """Deletes all profiles that have been recorded (e.g. heap profiles, cpu profiles...)"""
    self._cleared_heap_profiles = False

    def response_handler(response):
      self._cleared_heap_profiles = True

    self._communicator.send_cmd('Profiler.clearProfiles', {}, response_handler)
    wait_until(lambda: self._cleared_heap_profiles)

  def get_heap_profile(self):
    """Returns raw heap profiling data"""
    self._first_profile_id = None

    def headers_response_handler(response):
      self._first_profile_id = response['result']['headers'][0]['uid']

    self._communicator.send_cmd('Profiler.getProfileHeaders', {}, headers_response_handler)
    wait_until(lambda: self._first_profile_id)
    logging.info('Profile ID: %i' % self._first_profile_id)

    self._heap_profile_chunks = []
    self._heap_profile_data_recorded = False

    def heap_snapshot_data_callback(response):
      if response['method'] == 'Profiler.addHeapSnapshotChunk':
        self._heap_profile_chunks.append(response['params']['chunk'])
      elif response['method'] == 'Profiler.finishHeapSnapshot':
        self._heap_profile_data_recorded = True

    self._communicator.add_domain_callback('Profiler', 'heap_snapshot_data', heap_snapshot_data_callback)
    self._communicator.send_cmd('Profiler.getProfile', {'type': 'HEAP', 'uid': self._first_profile_id})

    wait_until(lambda: self._heap_profile_data_recorded)
    self._communicator.remove_domain_callback('Profiler', 'heap_snapshot_data')

    return ''.join(self._heap_profile_chunks)

  # --------------------------------------------------------------------------
  # DEBUGGER
  # --------------------------------------------------------------------------

  def enable_debugging(self):
    """Enables debugging, which lets you set JS breakpoints. Also required for doing heap profiles"""
    if self._debugging_enabled:
      logging.error('Debugging already enabled')
      return

    def start_callback(m):
      self._debugging_enabled = True

    self._communicator.send_cmd('Debugger.enable', {}, start_callback)
    wait_until(lambda: self._debugging_enabled)

  def disable_debugging(self):
    if not self._debugging_enabled:
      logging.error('Debugging not enabled')
      return

    def stop_callback(m):
      self._debugging_enabled = False

    self._communicator.send_cmd('Debugger.disable', {}, stop_callback)
    self._debugging_enabled = False

  # --------------------------------------------------------------------------
  # TIMELINE
  # --------------------------------------------------------------------------

  def start_timeline_monitoring(self, callback):
    """
    Enables monitoring of timeline events, including:
      - Resource requests
      - Paint events
      - GC Events
      ...and more
    """

    if self._timeline_started:
      logging.error('Timeline monitoring already started')
      return

    def start_callback(m):
      self._timeline_started = True

    self._communicator.add_domain_callback('Timeline', 'timeline_event', callback)
    self._communicator.send_cmd('Timeline.setIncludeMemoryDetails', {'enabled': True})
    self._communicator.send_cmd('Timeline.start', {}, start_callback)
    wait_until(lambda: self._timeline_started)

  def stop_timeline_monitoring(self):
    if not self._timeline_started:
      logging.error('Timeline monitoring not started')
      return

    def stop_callback(m):
      self._timeline_started = False

    self._communicator.send_cmd('Timeline.stop', {}, stop_callback)
    self._communicator.remove_domain_callbacks('Timeline')
    wait_until(lambda: not self._timeline_started)

  # --------------------------------------------------------------------------
  # NETWORK
  # --------------------------------------------------------------------------

  def start_network_monitoring(self, callback):
    """
    Enables processing of network events via the specified callback.

    Network events give information about:
    - Resource requests
    - Resorce responses
    - Resource data transfer progress
    """

    if self._network_enabled:
      logging.error('Network monitoring already enabled')
      return

    def start_callback(m):
      self._network_enabled = True

    self._communicator.add_domain_callback('Network', 'network_event', callback)
    self._communicator.send_cmd('Network.enable', {}, start_callback)
    wait_until(lambda: self._network_enabled)

  def stop_network_monitoring(self):
    if not self._network_enabled:
      logging.error('Network monitoring not enabled')
      return

    def stop_callback(m):
      self._network_enabled = False

    self._communicator.send_cmd('Network.disable', {}, stop_callback)
    self._communicator.remove_domain_callbacks('Network')
    wait_until(lambda: not self._network_enabled)

  @memoize
  def can_clear_http_cache(self):
    """Returns true if browser supports clearing the cache via remote debugging protocol"""
    def response_handler(response):
      self._can_clear_cache = response['result']['result']

    self._communicator.send_cmd('Network.canClearBrowserCache', {}, response_handler)

    wait_until(lambda: self._can_clear_cache != None)
    return self._can_clear_cache

  def clear_http_cache(self):
    self._cache_clear_complete = False

    def response_handler(response):
      if 'error' in response:
        logging.error('Error received: ' + pformat(response['error']))
      else:
        self._cache_clear_complete = True

    self._communicator.send_cmd('Network.clearBrowserCache', {}, response_handler)
    wait_until(lambda: self._cache_clear_complete)

  def clear_cookies(self):
    self._cookie_clear_complete = False

    def response_handler(response):
      if 'error' in response:
        logging.error('Error received: ' + pformat(response["error"]))
      else:
        self._cookie_clear_complete = True

    self._communicator.send_cmd('Network.clearBrowserCookies', {}, response_handler)
    wait_until(lambda: self._cookie_clear_complete)

  # --------------------------------------------------------------------------
  # PAGE
  # --------------------------------------------------------------------------

  def start_page_event_monitoring(self, callback):
    """
    Allows processing of page events via the given callback.

    Page events include:
    - page load
    - domcontent
    - frame navigated
    :param type callback: <description of param>
    :return: eiwojfei
    """

    if self._page_events_enabled:
      logging.error('Page events already being monitored')
      return
    def start_callback(m):
      self._page_events_enabled = True

    self._communicator.add_domain_callback('Page', 'page_event', callback)
    self._communicator.send_cmd('Page.enable', {}, start_callback)

    wait_until(lambda: self._page_events_enabled)

  def stop_page_event_monitoring(self):
    if not self._page_events_enabled:
      logging.error('Page events not being monitored')
      return

    def stop_callback(m):
      self._page_events_enabled = False

    self._communicator.send_cmd('Page.disable', {}, stop_callback)
    wait_until(lambda: not self._page_events_enabled)
    self._communicator.remove_domain_callbacks('Page')

  def navigate_to(self, url):
    """Navigates the browser window to the given url"""
    self._navigated = False

    def response_handler(response):
      self._navigated = True

    self._communicator.send_cmd('Page.navigate', {'url': url}, response_handler)
    wait_until(lambda: self._navigated)

  # ----------------
  # Form Interaction
  # ----------------

  def set_field_value(self, field_id, value):
    js = 'document.getElementById("{0}").value = "{1}"'.format(field_id, value)
    self.run_js(js, False)

  def click_button(self, button_id):
    js = 'document.getElementById("{0}").click()'.format(button_id)
    self.run_js(js, False)

  def dispatch_event(self, params):
    js_lines = ['e = document.createEvent("HTMLEvents")', 'e.initEvent("{0}", true, true)'.format(params['event-type'])]

    if 'id' in params:
      js_lines.append('document.getElementById("{0}").dispatchEvent(e)'.format(params['id']))
    else:
      js_lines.append('document.getElementsByClassName("{0}")[0].dispatchEvent(e)'.format(params['class']))

    js = ';'.join(js_lines)

    self.run_js(js, False)

  def click_link(self, params):
    js_lines = []

    js_lines.append('var f = document.createElement("form")')

    if "id" in params:
      js_lines.append('f.action = document.getElementById("{0}").href'.format(kwargs['id']))
    else:
      js_lines.append('f.action = document.getElementsByClassName("{0}")[0].href'.format(kwargs['class']))

    js_lines.append('document.body.appendChild(f)')
    js_lines.append('f.submit()')

    js = ';'.join(js_lines)
    self.run_js(js, False)

  def submit_form_by_id(self, form_id):
    js = 'document.getElementById("{0}").submit()'.format(form_id)
    self.run_js(js, False)

  # ---
  # CSS
  # ---

  def start_css_selector_profiling(self):
    if self._css_profiling_started:
      logging.error('CSS Profiling already started')
      return

    def response_handler(response):
      self._css_profiling_started = True

    self._communicator.send_cmd('CSS.startSelectorProfiler', {}, response_handler)
    wait_until(lambda: self._css_profiling_started)

  def stop_css_selector_profiling(self):
    if not self._css_profiling_started:
      logging.error('CSS selector profiling not started')
      return

    def response_handler(response):
      self._css_profiling_started = False
      self._css_profile = response

    self._communicator.send_cmd('CSS.stopSelectorProfiler', {}, response_handler)
    wait_until(lambda: not self._css_profiling_started)
    return self._css_profile

  # ----------------
  # Device/Browser Detection
  # ----------------

  @memoize
  def get_user_agent(self):
    return self.run_js('navigator.userAgent')

  @memoize
  def _device_is_ios(self):
    return 'iPhone' in self.get_user_agent() or 'iPod' in self.get_user_agent() or 'iPad' in self.get_user_agent()

  @memoize
  def _device_is_android(self):
    return 'Android' in self.get_user_agent()

  @memoize
  def get_os_name(self):
    if self._device_is_ios():
      return 'iOS'
    elif self._device_is_android():
      return 'Android'
    else:
      return 'Non-mobile OS'

  @memoize
  def get_os_version(self):
    if self._device_is_android():
      return re.search('Android\s+([\d\.]+)',self.get_user_agent()).groups()[0]
    elif self._device_is_ios():
      start = self.get_user_agent().index('OS')
      return self.get_user_agent()[start + 3, start + 6].replace('_', '.')
    else:
      return ''

  @memoize
  def get_browser_name(self):
    if self._device_is_ios():
      if not 'Safari' in self.get_user_agent():
        logging.error('Connected to non-Safari browser on iOS via remote debugging, this should not be possible')
      return 'Mobile Safari'
    elif self._device_is_android():
      if not 'Chrome' in self.get_user_agent():
        logging.error('Connected to non-Chrome browser on Android via remote debugging, this should not be possible')
      return 'Chrome for Android'
    else:
      return 'Non-mobile browser'

  @memoize
  def get_browser_version(self):
    if self._device_is_ios():
      return re.search('Version/([0-9\.]+)', self.get_user_agent()).groups()[0]
    elif self._device_is_android():
      return re.search('Chrome/([0-9\.]+)', self.get_user_agent()).groups()[0]
    else:
      return ''





