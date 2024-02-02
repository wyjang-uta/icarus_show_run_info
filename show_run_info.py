#!/usr/bin/python2
'''
Author: Wooyoung Jang (University of Texas at Arlington)
Date: Jan. 18. 2024

Purpose:
    Make a summary of runs by receiving the number of runs the user wants to 
  investigate as input, and starting from the most recent run, iterate 
  backward, printing run number, start time, end time, etc. The data is 
  obtained by parsing the DAQInterface logs.
    The separator used to distinguish each run log block is the string
      "BOOT transition underway"
    This script works with python 2.7.5

Usage:
  $ python show_run_info.py <number of runs>
'''

import os
import re
import time
import datetime
import math
import sys

# from stackoverflow.com
#   https://stackoverflow.com/questions/2301789/how-to-read-a-file-in-reverse-order
def reverse_readline(filename, buf_size=8192):
  """A generator that returns the lines of a file in reverse order"""
  with open(filename, 'rb') as fh:
    segment = None
    offset = 0
    fh.seek(0, os.SEEK_END)
    file_size = remaining_size = fh.tell()
    while remaining_size > 0:
      offset = min(file_size, offset + buf_size)
      fh.seek(file_size - offset)
      buffer = fh.read(min(remaining_size, buf_size))
      # remove file's last "\n" if it exists, only for the first buffer
      if remaining_size == file_size and buffer[-1] == '\n':
        buffer = buffer[:-1]
      remaining_size -= buf_size
      lines = buffer.split('\n')
      # append last chunk's segment to this chunk's last line
      if segment is not None:
        lines[-1] += segment
      segment = lines[0]
      lines = lines[1:]
      # yield lines in this chunk except the segment
      for line in reversed(lines):
        # only decode on a parsed line, to avoid utf-8 decode error
        yield line
    # Don't yield None if the file was empty
    if segment is not None:
      yield segment

def convert_to_unix_timestamp(time_info):
  try:
    struct_time = time.strptime(time_info, "%a %b %d %H:%M:%S %Z %Y")
    unix_timestamp = int(time.mktime(struct_time))
    return unix_timestamp
  except ValueError:
    return None

def format_time(time_info):
  if time_info:
    datetime_object = datetime.datetime.strptime(time_info, "%a %b %d %H:%M:%S %Z %Y")
    total_seconds = datetime_object.second + datetime_object.minute * 60 + datetime_object.hour * 3600

    # Round seconds and update datetime_object
    rounded_minutes, remaining_seconds = divmod(total_seconds, 60)
    rounded_hours, remaining_minutes = divmod(rounded_minutes, 60)
    datetime_object = datetime_object.replace(second=0, minute=remaining_minutes, hour=rounded_hours)

    # Check if the hour rolled over to the next day
    if rounded_hours == 24:
      datetime_object = datetime_object.replace(day=datetime_object.day + 1, hour=0)

      # Check if the day rolled over to the next month
      if datetime_object.day == 1:
        datetime_object = datetime_object.replace(month=datetime_object.month + 1)

        # Check if the month rolled over to the next year
        if datetime_object.month == 13:
          datetime_object = datetime_object.replace(year=datetime_object.year + 1, month=1)

    formatted_time = datetime_object.strftime("%m/%d/%Y %H:%M")
    return formatted_time
  else:
    return None

def print_runblock(block_content):
  run_block = []
  run_block.append(''.join(block_content))
  print(run_block[0])

def parse_runblock(block_content):
  is_run_number_issued=False
  for line in block_content:
    if 'BOOT transition underway' in line:
      boot_start_time_info = re.search(r'\w+ \w+ [ 1-9]\d? \d+:\d+:\d+ \w+ \d{4}', line)
      boot_start_time_info = boot_start_time_info.group()
      formatted_boot_start_time = format_time(boot_start_time_info)
      boot_start_unix_timestamp = convert_to_unix_timestamp(boot_start_time_info)
      print "BOOT start time         : ", boot_start_unix_timestamp, "(", formatted_boot_start_time, "[CT] )"
    elif 'BOOT transition complete' in line:
      boot_complete_time_info = re.search(r'\w+ \w+ [ 1-9]\d? \d+:\d+:\d+ \w+ \d{4}', line)
      boot_complete_time_info = boot_complete_time_info.group()
      formatted_boot_complete_time = format_time(boot_complete_time_info)
      boot_complete_unix_timestamp = convert_to_unix_timestamp(boot_complete_time_info)
      print "BOOT complete time      : ", boot_complete_unix_timestamp, "(", formatted_boot_complete_time, "[CT] )"
    elif 'CONFIG transition underway' in line:
      config_transition_time_info = re.search(r'\w+ \w+ [ 1-9]\d? \d+:\d+:\d+ \w+ \d{4}', line)
      config_transition_time_info = config_transition_time_info.group()
      formatted_config_transition_time = format_time(config_transition_time_info)
      config_transition_unix_timestamp = convert_to_unix_timestamp(config_transition_time_info)
      print "CONFIG transition time  : ", config_transition_unix_timestamp, "(", formatted_config_transition_time, "[CT] )"
    elif 'Config name:' in line:
      config_value = line.split(":")[1].strip()
      print "Config                  : ",config_value
    elif 'CONFIG transition complete' in line:
      config_complete_time_info = re.search(r'\w+ \w+ [ 1-9]\d? \d+:\d+:\d+ \w+ \d{4}', line)
      config_complete_time_info = config_complete_time_info.group()
      formatted_config_complete_time = format_time(config_complete_time_info)
      config_complete_unix_timestamp = convert_to_unix_timestamp(config_complete_time_info)
      print "CONFIG complete time    : ", config_complete_unix_timestamp, "(", formatted_config_complete_time, "[CT] )"
    elif 'START transition complete' in line:
      is_run_number_issued=True
      match = re.search(r'(\d+)$', line)
      run_number = match.group()
      print "Run number              : ",run_number

      run_start_time_info = re.search(r'\w+ \w+ [ 1-9]\d? \d+:\d+:\d+ \w+ \d{4}', line)
      run_start_time_info = run_start_time_info.group()
      formatted_start_time = format_time(run_start_time_info)
      run_start_unix_timestamp = convert_to_unix_timestamp(run_start_time_info)
      print "Run START timestamp     : ", run_start_unix_timestamp, "(", formatted_start_time, "[CT] )"
    elif 'STOP transition complete' in line:
      run_stop_time_info      = re.search(r'\w+ \w+ [ 1-9]\d? \d+:\d+:\d+ \w+ \d{4}', line)
      run_stop_time_info      = run_stop_time_info.group()
      formatted_stop_time     = format_time(run_stop_time_info)
      run_stop_unix_timestamp = convert_to_unix_timestamp(run_stop_time_info)
      print "Run END timestamp       : ", run_stop_unix_timestamp, "(", formatted_stop_time, "[CT] )"
    elif 'RECOVER transition complete' in line:
      run_recover_time_info      = re.search(r'\w+ \w+ [ 1-9]\d? \d+:\d+:\d+ \w+ \d{4}', line)
      run_recover_time_info      = run_recover_time_info.group()
      formatted_recover_time     = format_time(run_recover_time_info)
      run_recover_unix_timestamp = convert_to_unix_timestamp(run_recover_time_info)
      print "Run RECOVERED timestamp : ", run_recover_unix_timestamp, "(", formatted_recover_time, "[CT] )"
    elif 'TERMINATE transition complete' in line:
      run_terminate_time_info      = re.search(r'\w+ \w+ [ 1-9]\d? \d+:\d+:\d+ \w+ \d{4}', line)
      run_terminate_time_info      = run_terminate_time_info.group()
      formatted_terminate_time     = format_time(run_terminate_time_info)
      run_terminate_unix_timestamp = convert_to_unix_timestamp(run_terminate_time_info)
      print "Run TERMINATED timestamp: ", run_terminate_unix_timestamp, "(", formatted_terminate_time, "[CT] )"

def usage():
  print "Usage: show_run_info <number of runs>"

def main():
  if len(sys.argv) == 1:
    run_limit = 1
  elif len(sys.argv) == 2:
    run_limit = int(sys.argv[1])
  else:
    usage()
    sys.exit(1)

  run_count = 0
  run_block = []
  block_content = []

  line_count = 0
  for line in reverse_readline('DAQInterface_partition1.log'):
    if run_count >= run_limit:
      break

    block_content.append(line+'\n')
    line_count = line_count + 1

    if 'BOOT transition underway' in line:
      block_content.reverse()
      run_block.append(block_content)
      run_count = run_count + 1
      block_content = []

  for i in range(run_limit-1, -1, -1):    # loop is reversed in order to print the latest run show up at the end
    if i+1 % 10 == 1 and i % 100 != 11:
      suffix = "st"
    elif i+1 % 10 == 2 and i % 100 != 12:
      suffix = "nd"
    elif i+1 % 10 == 3 and i % 100 != 13:
      suffix = "rd"
    else:
      suffix = "th"
    print '-------------------- {}{} Run Log Block --------------------'.format(i+1,suffix)
    parse_runblock(run_block[i])

if __name__ == "__main__":
  main()
