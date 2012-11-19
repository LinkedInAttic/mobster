"""
Helper for getting html directory path
"""

import pkg_resources

def generate_html_dir():
  """ Return the html directory. """
  return pkg_resources.resource_filename('linkedin.mobster.har.visualization.html', None)