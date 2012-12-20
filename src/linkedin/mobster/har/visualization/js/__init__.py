"""
Helper for getting js directory path
"""

import pkg_resources

def generate_js_dir():
  """ Return the js directory. """

  return pkg_resources.resource_filename('linkedin.mobster.har.visualization.js', None)