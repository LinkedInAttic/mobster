import logging

main_log = logging.getLogger(__name__)
main_log.setLevel(logging.WARN)

log_file = '/var/tmp/mobster.log'
with open(log_file, 'w'):
  pass
file_hdlr = logging.FileHandler(log_file)
file_hdlr.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
file_hdlr.setLevel(logging.WARN)
main_log.addHandler(file_hdlr)

stream_hdlr = logging.StreamHandler()
stream_hdlr.setLevel(logging.WARN)
stream_hdlr.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
main_log.addHandler(stream_hdlr)
