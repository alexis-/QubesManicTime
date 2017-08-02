from usage_groups import *

class mt_state:
  def load(self):
    self.auth_token = None
    self.usage_timeline = None
    self.program_timeline = None
    self.program_groups = []

  def save(self):
    return None

class mt_client:
  api_path = None
  mt_state = None
  

  def __init__(self):
    self.mt_state = mt_state()
    # Go to handshake

  def api_handshake(self):
    # Check if need auth
    # Save api paths
    return None

  def api_auth_token(self):
    # Save auth token
    return None

  def api_list_timelines(self):
    # Do we need to publish ?
    # Check match mt_state
    return None

  def api_publish_timelines(self):
    # Save mt_state
    return None

  def api_get_timeline(self, timeline):
    # Get max entities (group)
