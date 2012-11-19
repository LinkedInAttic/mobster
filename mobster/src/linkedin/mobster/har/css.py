from heapq import nlargest

from linkedin.mobster.utils import memoize

class CSSProfileParser(object):
  """
  Parses CSS selector profile data and extracts important features
  """

  def __init__(self, css_selector_data):
    """
      Format of the css selector data:

      {
        "totalTime": [total processing time for CSS selectors],
        [
          {
            "selector": [selector name],
            "url": [url of resource containing css rule],
            "lineNumber": [line number of rule],
            "time": [time contribution to browser running time],
            "hitCount": [# of times rule was considered a possible match],
            "matchCount": [# of times rule was a match]
          }
          ...
        ]
      }
    """
    self.rules = css_selector_data['result']['profile']['data']
    self.total_time = css_selector_data['result']['profile']['totalTime']

  @memoize
  def get_rules_longest_time(self, number_results):
    """Returns the rules which use the most browser running time"""
    return nlargest(number_results, self.rules, key=lambda profile_entry: profile_entry['time'])

  @memoize
  def get_rules_worst_match_ratio(self, number_results):
    """Returns the rules which have the worst ratio of hits to actual matches"""
    return nlargest(number_results, self.rules, key=lambda profile_entry: float(profile_entry['matchCount'])/profile_entry['hitCount'])

  @memoize
  def get_rules_most_misses(self, number_results):
    """Returns the rules which have the largest difference between matches and hits"""
    return nlargest(number_results, self.rules, key=lambda profile_entry: profile_entry['hitCount'] - profile_entry['matchCount'])


  @memoize
  def get_css_stats(self):
    try:
      time_consuming_rule = self.get_rules_longest_time(1)[0]
      most_misses_rule = self.get_rules_most_misses(1)[0]
    except:
      # Set both to be None if there are no css rules
      time_consuming_rule = None
      most_misses_rule = None

    return {
      "_totalTime": self.total_time,
      "_mostTimeConsumingRule": time_consuming_rule,
      "_mostMissesRule": most_misses_rule
    }




