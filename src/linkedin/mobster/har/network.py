from collections import defaultdict
import logging

from linkedin.mobster.utils import format_time

log = logging.getLogger(__name__)

class NetworkEventHandler(object):
  def __init__(self):
    # request start times in seconds
    self._request_start_times = {}

    # the following dicts use request ids as keys
    self._request_start_times = defaultdict(lambda: -1)
    self._page_refs = defaultdict(lambda: '_')
    self._server_ips = defaultdict(lambda: '_')
    self._connection_ids = defaultdict(lambda: '_')
    self._resource_timings = defaultdict(self._default_resource_timing_value)
    self._requests = defaultdict(self._default_request_value)
    self._responses = defaultdict(self._default_response_value)
    self._caches = defaultdict(self._default_cache_value)
    self._data_packet_notifications = defaultdict(list)
    self._response_sizes = defaultdict(lambda: 0)
    self._response_encoded_sizes = defaultdict(lambda: 0)

    self.primary_page_id = 'page_1'

  # --------------
  # Initialization
  # --------------

  def _default_resource_timing_value(self):
    """
    Create initial value of resource timings object. We default to -1, since in the HAR format it signifies
    that the field was not applicable. This way, it is guaranteed that the output is valid even if the browser
    does not provide certain information (e.g. requesting about:blank does not have a receive time).
    """
    timing_metrics = ['blocked', 'dns', 'connect', 'send', 'wait', 'receive', 'ssl']
    return dict(zip(timing_metrics, len(timing_metrics) * [-1]))

  def _default_request_value(self):
    return {
      'method': '_',
      'url': '_',
      'httpVersion': '_',
      'cookies': [],
      'headers': [],
      'queryString': [],
      'headersSize': -1,
      'bodySize': 0
    }

  def _default_response_value(self):
    return {
      'status': -1,
      'statusText': '_',
      'httpVersion': '_',
      'cookies': [],
      'headers': [],
      'content': self._default_content_value(),
      'redirectURL': '',
      'headersSize': -1,
      'bodySize': 0
    }

  def _default_cache_value(self):
    return {
      'beforeRequest': None,
      'afterRequest': None
    }

  def _default_content_value(self):
    return  {
      'size': 0,
      'compression': '-99999',
      'mimeType': '_',
      'text': '_'
    }

  # ---------
  # Accessors
  # ---------

  def get_first_request_time(self):
    """Returns the time, in seconds, when the first resource request is initiated."""
    return min(self._request_start_times.values())

  # -----------------------------
  # HAR Resource Entry Generation
  # -----------------------------

  def _total_resource_time(self, req_id):
    """Returns the total time taken for the request corresponding to the given request ID"""
    timings = self._resource_timings[req_id]
    timing_values = timings.values()
    non_zero_timings = filter(lambda x: x> 0, timing_values)
    return int(sum(non_zero_timings))

  def _make_entry(self, req_id):
    """Creates the HAR resource entry corresponding to the given request ID"""

    return {
      'pageref': self.primary_page_id,
      'startedDateTime': format_time(self._request_start_times[req_id]),
      'time': self._total_resource_time(req_id),
      'request': self._requests[req_id],
      'response': self._responses[req_id],
      'cache': self._caches[req_id],
      'timings': self._resource_timings[req_id],
      'serverIPAddress': self._server_ips[req_id],
      'connection': self._connection_ids[req_id]
    }

  def make_entry_list(self):
    """
    Makes a list of HAR-formatted "entries", which correspond to resources requested by the page
    """
    request_ids_sorted_by_time = sorted(self._request_start_times, key=self._request_start_times.get)
    return [self._make_entry(req_id) for req_id in request_ids_sorted_by_time]


  # --------------
  # Event Handling
  # --------------

  def process_event(self, message):

    # the 'method' field of the message object will have the format X.Y, where X is the domain and Y is the command
    # e.g. 'Runtime.evaluate', 'Page.navigate', etc.
    message_type = message['method'].split('.')[1]

    {
      'requestWillBeSent': self.process_request_will_be_sent,
      'requestServedFromCache': self.process_request_served_from_cache,
      'responseReceived': self.process_response_received,
      'dataReceived': self.process_data_received,
      'loadingFinished': self.process_loading_finished,
      'requestServedFromMemoryCache': lambda m: None,
      'loadingFailed': lambda m: log.warning("Received loadingFailed message: \n{0}".format(m))
    }[message_type](message)

  def parse_msg(self, msg):
    """Transforms json message into a tuple (params, request_id, frame_id, timestamp)"""
    return (msg['params'], msg['params']['requestId'], msg['params']['frameId'], msg['params']['timestamp'])

  def process_request_will_be_sent(self, message):
    (params, request_id, frame_id, timestamp) = self.parse_msg(message)

    headers = [{'name': key, 'value' : value} for key, value in params['request']['headers'].iteritems()]
    self._requests[request_id]['headers'] = headers
    self._requests[request_id]['method'] = params['request']['method']

    self._requests[request_id]['url'] = params['request']['url']

    # we do this just in case the ResponseReceived event does not include timings (e.g. about:blank)
    self._request_start_times[request_id] = params['timestamp']

  def process_request_served_from_cache(self, message):
    log.info('Received request served from cache message: \n{0}'.format(message))

  def process_response_received(self, message):
    (params, request_id, frame_id, timestamp) = self.parse_msg(message)

    self._responses[request_id]['status'] = params['response']['status']
    self._responses[request_id]['statusText'] = params['response']['statusText']
    self._responses[request_id]['headersSize'] = -1

    headers = [{'name': key, 'value': value} for key, value in params['response']['headers'].iteritems()]
    self._responses[request_id]['headers'] = headers

    # timings are not included for about: url's
    if not self._requests[request_id]['url'].startswith('about:'):
      provided_timings = params['response']['timing']

      self._request_start_times[request_id] = provided_timings['requestTime']

      self._resource_timings[request_id]['blocked'] = max(provided_timings['dnsStart'], 0)

      self._resource_timings[request_id]['dns'] = \
        self.calc_timing(provided_timings['dnsStart'], provided_timings['dnsEnd'])

      self._resource_timings[request_id]['connect'] = \
        self.calc_timing(provided_timings['connectStart'], provided_timings['connectEnd'])

      self._resource_timings[request_id]['send'] = \
        self.calc_timing(provided_timings['sendStart'], provided_timings['sendEnd'])


  def process_data_received(self, message):
    self._data_packet_notifications[message['params']['requestId']].append(message['params'])

  def process_loading_finished(self, message):
    request_id = message['params']['requestId']
    self._data_packet_notifications[request_id].sort(key = lambda x: x['timestamp'])

    send_end = self._request_start_times[request_id] * 1000 + max(self._resource_timings[request_id]['blocked'], 0) \
                                                            + max(self._resource_timings[request_id]['dns'], 0)     \
                                                            + max(self._resource_timings[request_id]['connect'], 0) \
                                                            + max(self._resource_timings[request_id]['send'], 0)

    # don't bother recording timing/size info for 'about:XXXX' url's
    if not self._requests[request_id]['url'].startswith('about:'):
      data_packet_infos = self._data_packet_notifications[request_id]

      if len(data_packet_infos):
        first_data_timestamp = self._data_packet_notifications[request_id][0]['timestamp']
        last_data_timestamp = self._data_packet_notifications[request_id][-1]['timestamp']
        self._resource_timings[request_id]['wait'] = int(first_data_timestamp * 1000 - send_end)
        self._resource_timings[request_id]['receive'] = int(last_data_timestamp * 1000 - first_data_timestamp * 1000)
      else:
        self._resource_timings[request_id]['wait'] = int(message['params']['timestamp'] * 1000 - send_end)
        self._resource_timings[request_id]['receive'] = 0

      for packet_info in data_packet_infos:
        self._response_sizes[request_id] += packet_info['dataLength']
        self._response_encoded_sizes[request_id] += packet_info['encodedDataLength']

      self._responses[request_id]['bodySize'] = self._response_sizes[request_id]
      self._responses[request_id]['content']['size'] = self._response_sizes[request_id]
      self._responses[request_id]['content']['compression'] = self._response_sizes[request_id] - \
                                                              self._response_encoded_sizes[request_id]



  def calc_timing(self, start, end):
    """
    Returns the difference between start and end or -1 if the timing is not applicable to the current request (i.e.
    start and end are -1)
    """
    if start == -1 and end == -1:
      return -1
    else:
      return int(end - start)