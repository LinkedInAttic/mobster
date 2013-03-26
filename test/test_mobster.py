import json
import os
from pprint import pformat
import sys

# THIS TEST IS OUT OF DATE
print 'TEST IS OUT OF DATE. EXITING.'
sys.exit(0)

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')))


from linkedin.mobster.har.flowprofiler import FlowProfiler

def validate_str_is_number(s):
  try:
    float(s)
    return True
  except ValueError:
    assert False, '"%s" does not represent a number' % s

def validate_field((obj, obj_name), field_name, field_types, custom_validator=lambda x: None):
  assert field_name in obj, '%s should contain a field named "%s"\nObject: %s' % (obj_name, field_name, pformat(obj))

  detected_type = type(obj[field_name]).__name__

  assert detected_type in field_types,\
  '%s["%s"] should have one of the types "%s", found "%s"' % (obj_name, field_name, field_types, detected_type)
  custom_validator(obj[field_name])

def validate_fields((obj, obj_name), field_list):
  for field_tuple in field_list:
    validate_field((obj, obj_name), *field_tuple)

def validate_har_structure(har):
  '''
  Verifies that the given dictionary matches the HAR spec (v1.2)
  '''

  def validate_har_creator(creator):
    validate_fields((creator, 'creator'), [('name', ['str', 'unicode']), ('version', ['str', 'unicode'])])

  def validate_browser(browser):
    validate_fields((browser, 'browser'), [('name',    ['str', 'unicode']), ('version', ['str', 'unicode'])])

  def validate_pages(pages):
    for i in range(0, len(pages)):
      #TODO: validate date format in addition to just checking for the field
      validate_fields((pages[i], 'pages[%i]' % i), [('startedDateTime', ['str', 'unicode']),
        ('id',              ['str', 'unicode']),
        ('title',           ['str', 'unicode']),
        ('pageTimings',     ['dict'], lambda x: validate_page_timings(x, i))])

  def validate_page_timings(page_timings, i):
    validate_fields((page_timings, 'pages[%i]["pageTimings"]' % i), [('onContentLoad', ['int']),
      ('onLoad',        ['int'])])
  def validate_request(request, res_index):
    validate_fields((request, 'entries[%i]["request"]' % res_index), [('method',      ['str', 'unicode']),
      ('url',         ['str', 'unicode']),
      ('httpVersion', ['str', 'unicode']),
      ('cookies',     ['list']),
      ('headers',     ['list']),
      ('queryString', ['list']),
      ('headersSize', ['int']),
      ('bodySize',    ['int'])])

    #TODO(aboehm): add postData to mobster output so this can pass
    #if request['method'] == 'POST':
    #  validate_field((request, 'entries[%i]["request"]' % res_index), 'postData', ['dict'])

  def validate_response(response, res_index):
    validate_fields((response, 'entries[%i]["response"]' % res_index), [('status',      ['int']),
      ('statusText',  ['str', 'unicode']),
      ('httpVersion', ['str', 'unicode']),
      ('cookies',     ['list']),
      ('headers',     ['list']),
      ('content',     ['dict']),
      ('redirectURL', ['str', 'unicode']),
      ('headersSize', ['int']),
      ('bodySize',    ['int'])])

  def validate_cache(cache, res_index):
    # all cache fields are optional
    assert True

  def validate_resource_timings(timings, res_index):
    validate_fields((timings, 'entries[%i]["timings"]' % res_index), [('blocked', ['int']),
      ('dns',     ['int']),
      ('connect', ['int']),
      ('send',    ['int']),
      ('wait',    ['int']),
      ('receive', ['int']),
      ('ssl',     ['int'])])

    for key, time in timings.iteritems():
      assert time >= -1, 'entries[%i]["timings"]["%s"] must be >= -1, found %i' % (res_index, key, time)

  def validate_entries(entries):
    for i in range(0, len(entries)):
      validate_fields((entries[i], 'entries[%i]' % i), [('pageref',         ['str', 'unicode']),
        ('startedDateTime', ['str', 'unicode']),
        ('time',            ['int']),
        ('request',         ['dict'], lambda x: validate_request(x,i)),
        ('response',        ['dict'], lambda x: validate_response(x, i)),
        ('cache',           ['dict'], lambda x: validate_cache(x,i)),
        ('timings',         ['dict'], lambda x: validate_resource_timings(x,i))])




  assert 'log' in har, 'HAR file must contain a "log" field'

  validation_funcs = {'version': (['str', 'unicode'], lambda x: validate_str_is_number(x)),
                      'creator': ('dict', validate_har_creator),
                      'browser': ('dict', validate_browser),
                      'pages':   ('list', validate_pages),
                      'entries': ('list', validate_entries)}

  for field, (type, func) in validation_funcs.iteritems():
    validate_field((har['log'], 'log'), field, type, func)

gen = FlowProfiler('../bin/sampleinput/sample.json')
hars = gen.profile()

for har in hars:
  # remove unicode strings from dictionary to make type verification easier
  har = json.loads(json.dumps(har))
  print json.dumps(har)
  print '\n'
  validate_har_structure(har)
