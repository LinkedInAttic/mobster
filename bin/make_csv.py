#!/usr/bin/env python
"""Transforms the JSON output of Mobster (i.e. mobster.py) into a CSV file which can be more easily used for diff'ing"""


import argparse
import os
import json
import sys
import time

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')))

import dateutil.parser

from linkedin.mobster.utils import datetime_to_millis

def makeMetaDataBlock(file_name):
  lines = []
  lines.append('##BEGINMETADATA:')
  lines.append('HAR File::{0}'.format(os.path.abspath(file_name)))
  lines.append('##ENDMETADATA:')
  return '\n'.join(lines)


def makeDeviceInfoTable(har_data):
  lines = []
  lines.append('##BEGINTABLE:DEVICE INFORMATION')
  lines.append(','.join(['Device OS', 'Device OS Version', 'Browser', 'Browser Version']))
  lines.append(','.join([har_data[0]['log']['_os']['_name'], har_data[0]['log']['_os']['_version'], har_data[0]['log']['browser']['name'],
                         har_data[0]['log']['browser']['version']]))
  lines.append('##ENDTABLE:DEVICE INFORMATION:')
  return '\n'.join(lines)


def makeMemoryInfoTable(har_data):
  lines = []
  lines.append('##BEGINTABLE:MEMORY INFORMATION')
  lines.append(','.join(['Page Name', 'Max Allocated Heap', 'Max Used Heap', 'Number of GC Events']))
  for page_data in har_data:
    memory_stats = page_data['log']['pages'][0]['_memoryStats']
    lines.append(','.join([page_data['log']['pages'][0]['_pageName'], str(memory_stats['_maxTotalHeapSize']), str(memory_stats['_maxUsedHeapSize']),
                           str(page_data['log']['pages'][0]['_eventStats']['_gcEvents'])]))

  lines.append('##ENDTABLE:MEMORY INFORMATION')
  return '\n'.join(lines)


def makePageMetricsTable(har_data):
  lines = []
  lines.append('##BEGINTABLE: PAGE METRICS')
  lines.append(','.join(['Page Name', 'DOMContentLoad Time', 'OnLoad Time', 'Total CSS Time', 'Number of Style Recalculates', 'Number of Paints']))

  for page_data in har_data:
    page = page_data['log']['pages'][0]
    lines.append(','.join([page['_pageName'], str(page['pageTimings']['onContentLoad']), str(page['pageTimings']['onLoad']), str(page['_cssStats']['_totalTime']), str(page['_eventStats']['_styleRecalculates']), str(page['_eventStats']['_paints'])]))

  lines.append('##ENDTABLE: PAGE METRICS')
  return '\n'.join(lines)


def makeWaterfallTables(har_data):
  tables = []
  i = 0

  for page_data in har_data:
    tables.append(makeWaterfallSummaryTable(page_data, i))
    tables.append(makeWaterfallDetailsTable(page_data, i))
    i += 1

  return tables


def makeWaterfallSummaryTable(page_data, index):
  lines = []
  table_name = 'WATERFALL SUMMARY {0}'.format(index)
  lines.append('##BEGINTABLE: {0}'.format(table_name))
  lines.append(','.join(['Total Resource Load Time', 'Total Number of Resources', 'Total Page Size']))

  lines.append(','.join([str(totalResourceLoadTime(page_data)), str(len(page_data['log']['entries'])), str(totalPageSize(page_data))]))

  lines.append('##ENDTABLE: {0}'.format(table_name))
  return '\n'.join(lines)


def totalResourceLoadTime(page_data):
  entries = page_data['log']['entries']

  start_time = datetime_to_millis(dateutil.parser.parse(entries[0]['startedDateTime']))

  end_time = -1

  for entry in entries:
    end_time = max(end_time, datetime_to_millis(dateutil.parser.parse(entry['startedDateTime'])) + entry['time'])

  return end_time - start_time


def totalPageSize(page_data):
  total_size = 0

  for entry in page_data['log']['entries']:
    total_size += entry['response']['bodySize']

  return total_size


def makeWaterfallDetailsTable(page_data, index):
  lines = []

  table_name = 'WATERFALL DETAILS {0}'.format(index)
  lines.append('##BEGINTABLE: {0}'.format(table_name))
  lines.append(','.join(['Resource Name', 'Resource Load Time', 'Resource Size']))

  for entry in page_data['log']['entries']:
    lines.append(','.join([str(entry['request']['url']), str(entry['time']), str(entry['response']['bodySize'])]))

  lines.append('##ENDTABLE: {0}'.format(table_name))
  return '\n'.join(lines)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-r', '--har', required=True, help='Mobster output json to be converted to csv')
  parser.add_argument('-f', '--filename', help='Filename for output ')
  parser.add_argument('-d', '--outputdir', help='Directory to store output')
  args = parser.parse_args()

  filename = args.filename or 'mobster_tables_{0}.csv'.format(time.time())
  outputdir = args.outputdir or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'report')

  with open(args.har, 'r') as in_file:
    har_data = json.loads(in_file.read())

  with open(os.path.join(outputdir, filename), 'w') as out_file:
    out_file.write(('\n'*3).join([makeMetaDataBlock(args.har), makeDeviceInfoTable(har_data), makeMemoryInfoTable(har_data),
                                  makePageMetricsTable(har_data)] + makeWaterfallTables(har_data)))


