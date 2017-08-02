import json

from os import listdir, remove
from os.path import isfile, join

from random import randint

from datetime import datetime, timedelta

import copy

import dateutil.parser

from usage_groups import *
import localtimezone

# Where to look for samples ?
CONF_drop_location = '/home/user/QubesIncoming/dom0'
# Maximum allowed void between two consecutive sampling, which will be gapped
CONF_max_time_tear = 13

_DT = 'dt'
_SS = 'ss'
_AWAY = 'away'
_GROUP = 'group'
_TITLE = 'title'

class activity:
  def __init__(self, dict, start_dt):
    self.dict = dict
    self.dict['activityId'] = self.generate_activity_id(start_dt)
    self.dict['startTime'] = start_dt

  @staticmethod
  def generate_activity_id(dt):
    """Generates a unique activity id"""
    return int((dt - datetime(2013, 6, 5, tzinfo = localtimezone.Local)).total_seconds())

  def rebase(self, dt):
    return activity(copy.deepcopy(self.dict), dt)

  def is_same_kind(self, other):
    key = 'group' if 'group' in self.dict else 'groupId'
    return self.dict[key] == other.dict[key] and self.dict['displayName'] == other.dict['displayName']

  def end(self, end_dt):
    self.dict['endTime'] = end_dt

class qmt_processor:
  def __init__(self):
    self.last_dt = None
    self.last_usage = None
    self.last_program = None

  @staticmethod
  def filter_files(path, filename):
    """Filters in 'qmt_*.json' files"""
    return isfile(join(path, filename)) and filename.startswith('qmt_') and filename.endswith('.json')

  @staticmethod
  def list_qmt_files():
    """Lists all available samples"""
    return [join(CONF_drop_location, f) for f in listdir(CONF_drop_location) if qmt_processor.filter_files(CONF_drop_location, f)]

  @staticmethod
  def read_json_file(filepath):
    """Creates a dictionary from given json file"""
    with open(filepath, 'r') as f:
      return json.load(f)

  @staticmethod
  def load_all_qmt(qmt_files):
    """Loads all available samples in the form of a dictionary collection"""
    return [qmt_processor.read_json_file(f) for f in qmt_files]

  @staticmethod
  def order_chronologically(dict_collection):
    return sorted(dict_collection, key = lambda d: dateutil.parser.parse(d[_DT]))

  @staticmethod
  def get_usage_type(sample):
    """Determine computer usage type : Active, Away or Screensaver/Lockscreen"""
    if _SS in sample:
      return USG_SS_ON

    if _AWAY in sample:
      return USG_AWAY

    if _GROUP in sample and _TITLE in sample:
      return USG_ACTIVE

    raise ValueError('Invalid data: ' + str(sample))

  @staticmethod
  def hex_padding(hex):
    """Ensures hex values between 0-255 always form a two character string"""
    return '0' + hex if len(hex) == 1 else hex

  @staticmethod
  def generate_color():
    """Random color generator for activity groups"""
    r = hex(randint(0, 255))[2:]
    g = hex(randint(0, 255))[2:]
    b = hex(randint(0, 255))[2:]

    return qmt_processor.hex_padding(r) + qmt_processor.hex_padding(g) + qmt_processor.hex_padding(b)

  @staticmethod
  def make_usage_activity(sample, dt):
    """Turns raw data in ManicTime-formated computer usage activity
    Note: Usage groups are constant and thus not generated at runtime. See usage_groups.py"""
    usage_type = qmt_processor.get_usage_type(sample)

    act = {}
    act['displayName'] = USG[usage_type]['displayName']
    act['groupId'] = usage_type
    act['isActive'] = True

    return activity(act, dt)

  @staticmethod
  def make_program_activity(sample, dt):
    """Turns raw data in ManicTime-formated program activity"""
    if (not 'title' in sample) or (not 'group' in sample):
      return None

    act = {}
    act['displayName'] = sample['title']
    act['group'] = sample['group']
    act['isActive'] = True

    return activity(act, dt)

  @staticmethod
  def make_program_group(sample):
    """Turns raw data in ManicTime-formated program activity group"""
    grp = {}
    grp['displayName'] = sample['group']
    grp['displayKey'] = sample['group'] + ';' + sample['group']
    grp['color'] = qmt_processor.generate_color()
    grp['skipColor'] = False

    return grp

  @staticmethod
  def merge_program_group(groups, sample):
    groups[sample['group']] = qmt_processor.make_program_group(sample)

    return groups

  def commit(self, activity, activity_col, dt):
    if not activity:
      return activity_col

    activity.end(dt)
    activity_col.append(activity)

    return activity_col

  def check_continuity(self, mt_dict, usage, program, dt):
    # Preceding data is outdated, start anew
    if self.last_dt and dt > self.last_dt + timedelta(0, CONF_max_time_tear):
      mt_dict['usages'] = self.commit(self.last_usage, mt_dict['usages'], dt)
      mt_dict['programs'] = self.commit(self.last_program, mt_dict['programs'], dt)
      self.last_usage = usage
      self.last_program = program

      return mt_dict

    if usage and self.last_usage and not usage.is_same_kind(self.last_usage):
      mt_dict['usages'] = self.commit(self.last_usage, mt_dict['usages'], dt)
      self.last_usage = usage

    if program and self.last_program and not program.is_same_kind(self.last_program):
      mt_dict['programs'] = self.commit(self.last_program, mt_dict['programs'], dt)
      self.last_program = program

    return mt_dict

  def process_sample(self, mt_dict, sample):
    dt = dateutil.parser.parse(sample[_DT])

    usage = self.make_usage_activity(sample, dt)
    program = self.make_program_activity(sample, dt)

    mt_groups = self.merge_program_group(mt_dict['program_groups'], sample)
    mt_dict = self.check_continuity(mt_dict, usage, program, dt)

    if not self.last_usage:
      self.last_usage = usage

    if not self.last_program:
      self.last_program = program

    self.last_dt = dt

    return mt_dict

  def make_manic_pallatable(self, ordered_data):
    mt_dict = {}
    mt_dict['usages'] = []
    mt_dict['programs'] = []
    mt_dict['program_groups'] = {}

    for d in ordered_data:
      mt_dict = self.process_sample(mt_dict, d)

    if self.last_program and self.last_program.dict['startTime'] != self.last_dt:
      mt_dict['programs'] = self.commit(self.last_program, mt_dict['programs'], self.last_dt)
      self.last_program = self.last_program.rebase(self.last_dt)

    if self.last_usage and self.last_usage.dict['startTime'] != self.last_dt:
      mt_dict['usages'] = self.commit(self.last_usage, mt_dict['usages'], self.last_dt)
      self.last_usage = self.last_usage.rebase(self.last_dt)
    
    return mt_dict['usages'], mt_dict['programs'], mt_dict['program_groups']

  @staticmethod
  def clean_qmt_files(filepath_collection):
    for fp in filepath_collection:
      remove(fp)

  def process(self):
    qmt_files = self.list_qmt_files()
    data_col = self.load_all_qmt(qmt_files)
    data_col = self.order_chronologically(data_col)

    usages, programs, program_groups = self.make_manic_pallatable(data_col)

    mt = {}
    mt['usage'] = {}
    mt['usage']['activities'] = [ u.dict for u in usages ]
    mt['program'] = {}
    mt['program']['activities'] = [ p.dict for p in programs ]
    mt['program']['groups'] = program_groups.values()

    #self.clean_qmt_files(qmt_files)

    return mt

qmtp = qmt_processor()
print qmtp.process()
