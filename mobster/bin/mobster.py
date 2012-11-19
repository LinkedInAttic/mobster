#!/usr/bin/env python
"""Mobster is a command-line tool for profiling remote WebKit-based browsers via the
 WebKit remote debugging protocol. This script provides a simple way to use the tool
 to profile a single page and generate a HAR file containing the results"""

##
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')))
del os, sys
##

import argparse
import json
import os
import subprocess
import sys
import time

from linkedin.mobster.har.flowprofiler import FlowProfiler
from linkedin.mobster.har.merge import merge_by_average

DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'report')

if __name__ == '__main__':
  arg_parser = argparse.ArgumentParser()
  arg_parser.add_argument('-d', '--outputdir', help='Write JSON file to specified directory')
  arg_parser.add_argument('-f', '--filename', help="Used specified name for JSON file")
  arg_parser.add_argument('-u', '--urls', help='Comma separated URLs to profile')
  arg_parser.add_argument('-t', '--testfile', required=True, help='Use specified JSON test file to determine test actions')
  arg_parser.add_argument('-i', '--iterations', help='Do profiling task the specified number of times')
  arg_parser.add_argument('-a', '--average', action='store_true', help='Output the average results of the iterations')
  arg_parser.add_argument('-p', '--report', action='store_true', help='Call make_report.py to make a report and open it')

  args = arg_parser.parse_args()

  har_gen = FlowProfiler(args.testfile, int(args.iterations)) if args.iterations else FlowProfiler(args.testfile)

  # profiling_results is a list of lists containing HARs for each page in a run
  profiling_results = har_gen.profile()

  if args.average:
    chosen_result = [merge_by_average(page_results) for page_results in zip(*profiling_results)]
  else:
    chosen_result = profiling_results[-1]

  result_text = json.dumps(chosen_result)
  filename = args.filename or 'data_{0}.json'.format(int(time.time()))

  if args.outputdir:
    output_file = os.path.join(args.outputdir, filename)
  else:
    if not os.path.isdir(DEFAULT_OUTPUT_DIR):
      os.mkdir(DEFAULT_OUTPUT_DIR)

    output_file = os.path.join(DEFAULT_OUTPUT_DIR, filename)

  with open(output_file, 'w') as f:
    f.write(result_text)

  if args.report:
    cmd = [sys.executable, 'make_report.py', '-r', output_file, '-b']

    if args.outputdir:
      cmd.extend(['-d', args.outputdir])
    subprocess.call(cmd)
