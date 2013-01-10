from collections import defaultdict
import json
import logging
from pprint import pformat
from Queue import Queue
import sys
import threading
import urllib2

from ws4py.client.threadedclient import WebSocketClient

log = logging.getLogger(__name__)

class RemoteWebKitCommunicator(WebSocketClient):
  """
  Asynchronous interface for communicating with a remote WebKit-based browser via remote debugging
  protocol. Currently tested only on desktop and Android versions of Google Chrome.

  Chrome's documentation: https://developers.google.com/chrome-developer-tools/docs/remote-debugging
  Latest WebKit Protocol Spec: http://trac.webkit.org/browser/trunk/Source/WebCore/inspector/Inspector.json

  NOTE: The WebKit protocol spec may contain features unavailable in current WebKit browser releases

  """

  def __init__(self, page_num = 0, port = 9222):
    self._counter = 0
    self._response_callbacks = {}
    self._domain_callbacks = defaultdict(lambda: {})
    self._stopped = False
    self._command_queue = Queue()

    # Access list of open browser pages and pick the page with the specified index
    url = 'http://localhost:{0}/json'.format(port)
    try:
      response = urllib2.urlopen(url).read()
    except urllib2.URLError:
      log.error("Failed to connect. Please make sure a browser "   \
                "is running with WebKit remote debugging enabled.")
      sys.exit()

    page_info = json.loads(response)
    page = page_info[page_num]
    debug_ws_url = page['webSocketDebuggerUrl']

    super(RemoteWebKitCommunicator, self).__init__(debug_ws_url)
    self.start()

  def opened(self): pass
  def closed(self, code, reason=None): pass

  def received_message(self, messageData):
    """Called whenever the WebSocket receives a message"""
    response = json.loads(str(messageData))
    log.info('Received: \n{0}'.format(pformat(response)))

    if 'id' in response:
      id = response['id']
      self._response_callbacks[id](response)
    elif 'method' in response:
      callbacks = self._domain_callbacks[response['method'].split('.')[0]].values()
      for callback in callbacks: 
        callback(response)
    else:
      log.warn('Unrecognized message: {0}'.format(pformat(response)))


  def start(self):
    """
    Opens the WebSocket connection and starts a thread which continually sends commands as they appear in the queue.
    """

    if self._stopped:
      log.error('Connection has been closed')
      return

    self.connect()
    def send_commands():
      while True:
        cmd = self._command_queue.get()

        # None is our termination flag
        if cmd == None:
          self.close()
          break
        self.send(json.dumps(cmd))
        log.info('Sent: \n{0}'.format(pformat(cmd)))

    cmd_thread = threading.Thread(target=send_commands, args=())
    cmd_thread.setDaemon(True)
    cmd_thread.start()

  def send_cmd(self, method, params={}, callback=lambda x: None):
    """
    Sends a command to the browser. The given 'method' must be valid, or an error will be returned.
    Automatically adds a unique ID to the command. This allows the given callback to be called on
    all responses to the command which is sent.
    """

    cmd = self.generate_cmd(method, params)
    self._response_callbacks[cmd['id']] = callback
    self._command_queue.put(cmd)

  def add_domain_callback(self, domain, name, callback):
    """
    Adds a callback for responses based on their remote protocol domain. Will not be called
    for messages containing an ID. Common use case is timeline events, network events, etc.
    """
    self._domain_callbacks[domain][name] = callback

  def remove_domain_callback(self, domain, name):
    self._domain_callbacks[domain].pop(name)

  def remove_domain_callbacks(self, domain):
    self._domain_callbacks[domain].clear()

  def generate_cmd(self, method, params):
    """
    Constructs a command according to the WebKit remote protocol (to be sent as JSON)
    """
    # Give command a unique identifier so we can match callbacks
    self._counter += 1
    return {'id': self._counter, 'method': method, 'params': params}

  def stop(self):
    """
    Stops the sending and receiving threads
    """
    self._command_queue.put(None)
