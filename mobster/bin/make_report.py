#!/usr/bin/env python
"""Uses the output of Mobster (i.e. mobster.py) to create an HTML report featuring data tables and an HTTP waterfall chart"""

##
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')))
del os, sys
##

import argparse
import commands
import os
import time

from linkedin.mobster.utils import cmd_exists
from linkedin.mobster.har.visualization.report import make_html

LINUX_BROWSER_OPEN_CMD = 'xdg-open'
MAC_BROWSER_OPEN_CMD = 'open'

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-d', '--outputdir', help='Directory to store result in')
  parser.add_argument('-r', '--har', required=True, help='Use specified HAR instead of generating with phantomjs')
  parser.add_argument('-b', '--browser', action='store_true', help='Open HTML in browser after creation')
  parser.add_argument('-g', '--debug', action='store_true', help='Generate in debug mode, i.e. CDN script links will not be replaced with source')
  parser.add_argument('-f', '--filename', help='Filename for report')
  args = parser.parse_args()

  output_html = make_html(args.har, args.debug)

  output_dir = args.outputdir or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'report')
  if not os.path.isdir(output_dir):
    os.mkdir(output_dir)

  filename = args.filename or 'http_waterfall_{0}.html'.format(int(time.time()))

  with open(os.sep.join([output_dir, filename]), 'w') as output_handle:
    output_handle.write(output_html)

  if args.browser:
    if cmd_exists(LINUX_BROWSER_OPEN_CMD):
      browser_open_cmd = LINUX_BROWSER_OPEN_CMD
    else:
      browser_open_cmd = MAC_BROWSER_OPEN_CMD

    commands.getstatusoutput('%s %s' % (browser_open_cmd, os.sep.join([output_dir, filename])))




