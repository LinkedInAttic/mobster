import json
import os
import re
import urllib2

from linkedin.mobster.har.visualization.html import generate_html_dir
from linkedin.mobster.har.visualization.js import generate_js_dir

TEMPLATE_NAME = 'report.html'


def get_script_contents(script_name):
  file_name = os.sep.join([generate_js_dir(), script_name])
  assert os.path.isfile(file_name), 'File {0} does not exist'.format(file_name)

  with open(file_name) as script_file:
    return script_file.read()


def make_html(har_filename, debug=False):
  with open(har_filename, 'r') as f:
    file_json = json.loads(f.read())

  if type(file_json) != type([]):
    # we must paste a list of HAR files into the template, because that is what the JS expects
    file_json = [file_json]

  har_json_list = json.dumps(file_json)

  with open(os.sep.join([generate_html_dir(), TEMPLATE_NAME]), 'r') as template_handle:
    template_contents = template_handle.read()

  # replace all js script references with the contents of the files, so our output is standalone
  script_regex = r'<script\s+src\s*=[\'"]js/([^"\']+)[\'"]\s*>\s*</script>'
  scripts_to_substitute = re.findall(script_regex, template_contents)

  for script in scripts_to_substitute:
    replacement = '<script>{0}</script>'.format(get_script_contents(script))
    template_contents = re.sub(script_regex, replacement.replace("\\", "\\\\"), template_contents, 1)

  # if we're not using debug settings, dump all the JS from cdn links into the file
  if not debug:
    script_regex = r'<script\s+src\s*=[\'"](http[^"\']+)[\'"]\s*>\s*</script>'
    script_links_to_substitute = re.findall(script_regex, template_contents)

    for link in script_links_to_substitute:
      replacement = '<script>{0}</script>'.format(urllib2.urlopen(link).read())
      template_contents = re.sub(script_regex, replacement.replace("\\", "\\\\"), template_contents, 1)

  # insert the har json into the template
  return template_contents.replace('{{ har_json }}', har_json_list)