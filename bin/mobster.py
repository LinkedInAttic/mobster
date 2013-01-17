#!/usr/bin/env python
"""Mobster is a command-line tool for profiling remote WebKit-based browsers via the
WebKit remote debugging protocol. This script provides a simple way to use the tool
to profile a single page and generate a HAR file containing the results"""

import argparse
import commands
import json
import logging
import os
import subprocess
import sys
import time

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')))
  
from linkedin.mobster.har.flowprofiler import FlowProfiler
from linkedin.mobster.har.merge import merge_by_average
from linkedin.mobster.har.visualization.report import make_html
from linkedin.mobster.mobsterconfig import config
from linkedin.mobster.utils import cmd_exists

LINUX_BROWSER_OPEN_CMD = 'xdg-open'
MAC_BROWSER_OPEN_CMD = 'open'
DEFAULT_OUTPUT_DIR = \
  os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'report')
REPORT_FILE_TEMPLATE = 'http_waterfall_{0}.html'
HAR_FILE_TEMPLATE = 'data_{0}.json'
TIMESTAMP = int(time.time())

def run(args):
  """
  Run a test with the specified parameters, and return the HTTP Archive
  (HAR) File represented as a dictionary.
  """
  har_gen = FlowProfiler(args.testfile, int(args.iterations))   \
            if args.iterations else FlowProfiler(args.testfile)

  # profiling_results is a list of lists containing HARs for each page in a run
  profiling_results = har_gen.profile()

  if args.average:
    return [merge_by_average(page_results) \
            for page_results in zip(*profiling_results)]
  else:
    return profiling_results[-1]

def write_report(args):
  """
  Autogenerates an HTML report and writes it to a file, with location and input
  specified by the given arguments.
  """
  output_html = make_html(args.har or har_file_path(args), args.debug)

  with open(report_file_path(args), 'w') as output_handle:
    output_handle.write(output_html)
  
  if args.browser:
    open_browser(report_file_path(args))

def open_browser(file_path):
  """
  Open the specified file in the default web browser. Only works in Mac OS
  and Linux
  """
  if cmd_exists(LINUX_BROWSER_OPEN_CMD):
    browser_open_cmd = LINUX_BROWSER_OPEN_CMD
  else:
    browser_open_cmd = MAC_BROWSER_OPEN_CMD
  
  commands.getstatusoutput('{0} {1}'.format(browser_open_cmd, file_path))

def report_file_path(args):
  """
  Returns the path of the file where the report should be stored as specified
  by the arguments.
  """
  if args.reportoutput:
    return args.reportoutput
  else:
    if args.reportdirectory:
      output_dir = args.reportdirectory
    else:
      output_dir = DEFAULT_OUTPUT_DIR
      if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    filename = REPORT_FILE_TEMPLATE.format(TIMESTAMP)
    return os.sep.join([output_dir, filename])

def har_file_path(args):
  """
  Returns the path of the file where the HAR output should be stored as
  specified by the arguments.
  """
  if args.haroutput:
    return args.haroutput
  else:
    if args.hardirectory:
      output_dir = args.hardirectory
    else:
      output_dir = DEFAULT_OUTPUT_DIR
      if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    filename = HAR_FILE_TEMPLATE.format(TIMESTAMP)
    return os.sep.join([output_dir, filename])

def init_logging():
  log_file = '/var/tmp/mobster.log'

  # clear the log file
  with open(log_file, 'w'):
    pass

  # have all logging messages logged to a file
  logging.basicConfig(level=logging.DEBUG,
                      format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_file,
                      filemode='w')

  # print specific levels of log messages to the console
  console = logging.StreamHandler()
  console.setLevel(logging.DEBUG if config["DEBUG"] else logging.WARNING)
  formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
  console.setFormatter(formatter)
  logging.getLogger('').addHandler(console)


def parse_args():
  arg_parser = argparse.ArgumentParser()

  arg_parser.add_argument('-o', '--port', type=int, help='WebSocket port to use')
  arg_parser.add_argument('-d', '--debug', action='store_true', \
    help='Enable debug mode (prints logging messages)')

  arg_parser.add_argument('-t', '--testfile', \
    help='Perform test actions in specified JSON file')
  arg_parser.add_argument('-ho', '--haroutput', \
    help='Name of output HAR file')
  arg_parser.add_argument('-hd', '--hardirectory', \
    help='Directory to store output HAR file')
  arg_parser.add_argument('-i', '--iterations', \
    help='Do profiling task the specified number of times')
  arg_parser.add_argument('-a', '--average', action='store_true', \
    help='Output the average results of the iterations')

  arg_parser.add_argument('-p', '--report', action='store_true', \
    help='Generate HTML report')
  arg_parser.add_argument('-po', '--reportoutput', \
    help='Name of output HTML file')
  arg_parser.add_argument('-pd', '--reportdirectory', \
    help='Directory to store output HAR file')
  arg_parser.add_argument('-g', '--reportdebug', action='store_true', \
    help='Generate report in debug mode, i.e. CDN script links will not be' \
         'replaced with source')

  arg_parser.add_argument('-b', '--browser', action='store_true', \
    help='Open HTML report in browser after creation')
  
  # Used if and only if generating report with results from previous test
  arg_parser.add_argument('-r', '--har', \
    help="Used specified name for JSON file")
  
  return arg_parser.parse_args()

### ENTRY POINT ###
if __name__ == '__main__':
  args = parse_args()
  
  if args.port:
    config["WS_DEBUG_PORT"] = args.port
  if args.debug:
    config["DEBUG"] = True
  init_logging()
  
  if args.har:
    write_report(args)
  else:
    har_as_dict = run(args)
    
    with open(har_file_path(args), 'w') as f:
      f.write(json.dumps(har_as_dict))

    if args.report:
      write_report(args)
