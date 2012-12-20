

def merge_by_average(hars):
  """
  Returns a har file representing the average of multiple har files, each reprenting the same page request. The har
  files must represent loads of the same page for the result to make any sense. Page load times and resource load times
  are taken from the median result to ensure that an HTTP waterfall graph makes sense.
  """
  logs = map(lambda har: har['log'], hars)

  os_info_first = logs[0]['_os']
  browser_info_first = logs[0]['browser']
  creator_first = logs[0]['creator']
  assert all(log['_os'] == os_info_first and
             log['browser'] == browser_info_first and
             log['creator'] == creator_first for log in logs)

  avg_har = {"log": {}}
  avg_log = avg_har["log"]

  avg_log['_os'] = os_info_first
  avg_log['creator'] = creator_first
  avg_log['browser'] = browser_info_first
  avg_log['version'] = logs[0]['version']

  sorted(logs, key=lambda log: log['pages'][0]['pageTimings']['onLoad'])
  median_onload_log = logs[len(logs) / 2]

  avg_log['entries'] = median_onload_log['entries']

  avg_log['pages'] = []
  avg_log['pages'].append({})

  avg_log['pages'][0]['_cssStats'] = avg_css_stats([log['pages'][0]['_cssStats'] for log in logs])
  avg_log['pages'][0]['_memoryStats'] = avg_memory_stats([log['pages'][0]['_memoryStats'] for log in logs])
  avg_log['pages'][0]['_eventStats'] = avg_event_stats([log['pages'][0]['_eventStats'] for log in logs])
  avg_log['pages'][0]['_domNodeStats'] = median_onload_log['pages'][0]['_domNodeStats']
  avg_log['pages'][0]['pageTimings'] = median_onload_log['pages'][0]['pageTimings']

  for field, value in median_onload_log['pages'][0].iteritems():
    if type(value) == type("") or type(value) == type(u""):
      avg_log['pages'][0][field] = value


  return avg_har


def avg_css_stats(stats_list):
  """
  Returns averaged CSS stats from a list of the CSS stats of multiple runs. We return the average CSS totalTime and the
  max of the most time consuming and most misses rules from all the runs.
  """
  css_result = {}
  css_result['_totalTime'] = sum(stats['_totalTime'] for stats in stats_list) / len(stats_list)

  css_result['_mostTimeConsumingRule'] = max((stats['_mostTimeConsumingRule'] for stats in stats_list),
                                             key=lambda rule: rule['time'])
  css_result['_mostMissesRule'] = max((stats['_mostMissesRule'] for stats in stats_list),
                                      key=lambda rule: rule['hitCount'] - rule['matchCount'])
  return css_result

def avg_memory_stats(stats_list):
  """
  Returns averaged memory statistics from all the runs (_max* fields are calculated via taking the max as opposed
  to average)
  """
  mem_result = {}

  mem_result['_initialTotalHeapSize'] = sum(stats['_initialTotalHeapSize'] for stats in stats_list) / len(stats_list)
  mem_result['_maxTotalHeapSize'] = max(stats['_maxTotalHeapSize'] for stats in stats_list)

  mem_result['_initialUsedHeapSize'] = sum(stats['_initialUsedHeapSize'] for stats in stats_list) / len(stats_list)
  mem_result['_maxUsedHeapSize'] = max(stats['_maxUsedHeapSize'] for stats in stats_list)
  mem_result['_avgUsedHeapSize'] = sum(stats['_avgUsedHeapSize'] for stats in stats_list) / len(stats_list)

  mem_result['_maxJsEventListeners'] = max(stats['_maxJsEventListeners'] for stats in stats_list)
  mem_result['_maxNodes'] = max(stats['_maxNodes'] for stats in stats_list)
  mem_result['_maxDocuments'] = max(stats['_maxDocuments'] for stats in stats_list)

  return mem_result

def avg_event_stats(stats_list):
  """
  Returns an object containing simple averages of all the event stats
  """
  event_result = {}

  event_result['_styleRecalculates'] = sum(stats['_styleRecalculates'] for stats in stats_list) / len(stats_list)
  event_result['_gcEvents'] = sum(stats['_gcEvents'] for stats in stats_list) / len(stats_list)
  event_result['_paints'] = sum(stats['_paints'] for stats in stats_list) / len(stats_list)

  return event_result