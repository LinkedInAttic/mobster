import logging

from linkedin.mobster.utils import running_avg

timeline_event_blacklist = ['Program']

class TimelineEventHandler(object):
  def __init__(self):
    self.used_heap_init  = None
    self.used_heap_max  = -1
    self.used_heap_avg = -1
    self.max_documents = -1
    self.max_js_event_listeners = -1
    self.max_nodes = -1
    self.style_recalculates = 0
    self.paints = 0
    self.gc_events = 0

    self._used_heap_avg_calc = running_avg()

  def get_memory_stats(self):
    return {
      '_initialUsedHeapSize': self.used_heap_init,
      '_maxUsedHeapSize': self.used_heap_max,
      '_avgUsedHeapSize': self.used_heap_avg,

      '_maxDocuments': self.max_documents,
      '_maxJsEventListeners': self.max_js_event_listeners,
      '_maxNodes': self.max_nodes
    }

  def get_event_stats(self):
    """
    Contains counts of specific timeline events
    """
    return {
      '_paints': self.paints,
      '_styleRecalculates': self.style_recalculates,
      '_gcEvents': self.gc_events
    }

  def process_event(self, message):
    def helper(record):
      # don't examine events which are in the blacklist (but we still examine their children)
      if record['type'] not in timeline_event_blacklist:
        try:
          self.used_heap_init = self.used_heap_init or record['usedHeapSize']
          self._used_heap_avg_calc.next()
          self.used_heap_avg = self._used_heap_avg_calc.send(record['usedHeapSize'])

          self.used_heap_max = max(self.used_heap_max, record['usedHeapSize'])

          # The following statments keep track of metrics only available in Chrome 19+. Android Chrome is currently
          # at version 18, so we will not enable these until it is updated.

          #self.max_documents = max(self.max_documents, record['counters']['documents'])
          #self.max_js_event_listeners = max(self.max_js_event_listeners, record['counters']['jsEventListeners'])
          #self.max_nodes = max(self.max_nodes, record['counters']['nodes'])
        except KeyError, e:
          logging.warning('Could not find key {0} in response'.format(e.message))

        if record['type'] == 'GCEvent':
          self.gc_events += 1
        elif record['type'] == 'Paint':
          self.paints += 1
        elif record['type'] == 'RecalculateStyles':
          self.style_recalculates += 1

      if 'children' in record:
        for child in record['children']:
          helper(child)

    helper(message['params']['record'])
