from time import sleep
from datetime import datetime, timedelta
from os.path import join

# Shell exec, used for audio activity checks and data forwarding
from subprocess import check_output, call

import xlib_python
import xlib_native
import localtimezone

# Name of the timeline under which tracking will be saved
CONF_timeline = "laptop"
# Whether audio media playback (incl. videos) suspends idle monitoring
CONF_no_idle_during_audio = True
# Delay between each consecutive activity sampling (in esconds)
CONF_poll_delay = 5
# Delay between each consecutive data transfer (in esconds)
CONF_forward_delay = 60
# Inactivity delay before recording as being away (in seconds)
CONF_away_delay = 1 * 60
# Command run when moving samples to relay. Change your destination VM here
CONF_forward_cmd = "qvm-move-to-vm sys-services %s"
# Location where samples are stored before being moved to relay. Make sure folder exists
CONF_storage_location = "/home/alexis/.qmt"
# Debug logs ?
CONF_debug = False


def log(str):
  if CONF_debug:
    with open('debug.log', 'a+') as f:
      f.write(str + '\n')

def loop():
  # xlib_native class needs to free allocated resources, thus 'with'
  with xlib_native.xlib_native() as xnat:
    xpy = xlib_python.xlib_python()

    now = local_time()
    last_forward = now

    # TODO: There should be some kill or pause switch here...
    while 1:
      try:
        # Get up to date data
        idle_time, ss_on_libxss = xnat.query_screensaver_info()
        ss_on_xss = xpy.get_xscreensaver_status()
        is_audio_playing = query_audio_playback()

        ss_on = ss_on_libxss or ss_on_xss
        is_away = not is_audio_playing and idle_time >= CONF_away_delay * 1000

        # Eschew further querying if we are away, or computer is locked
        if is_away or ss_on_libxss or ss_on_xss:
          wdw_props = {}

        else:
          wdw_props = xpy.get_active_window()

        now = local_time()
      except Exception as e:
        log(str(e))
        sleep(1)
        continue
        
      # Build JSON from raw data
      data = build_data(wdw_props, ss_on, is_away, now)

      # Write JSON to file
      write_data(data, now)

      # Batch forward data to relay Domain
      last_forward = forward_data(now, last_forward)
      
      sleep(CONF_poll_delay)

def build_data(wdw_props, ss_on, is_away, now):
  dt = now.isoformat()

  if ss_on:
    return '{ "dt": "%s", "ss": 1 }' % dt

  if is_away:
    return '{ "dt": "%s", "away": 1 }' % dt

  # Properties are not uniform across domains:
  # dom0 is handled in a specific way, while domU-s may offer differing sementics depending on underlying OS
  if wdw_props[xlib_python._PROP_WM_MACHINE] == "dom0":
    group = wdw_props[xlib_python._PROP_WM_CLASS]
    title = "[dom0] " + wdw_props[xlib_python._PROP_WM_NAME]

  else:
    cls = wdw_props[xlib_python._PROP_WM_CLASS]
    domain = wdw_props[xlib_python._PROP_DOMU_DOMAIN]
    title = "[" + domain + "] " + wdw_props[xlib_python._PROP_DOMU_TITLE2]

    # We can extract app name from class field
    # e.g. 'work:firefox-browser'
    if cls.startswith(domain + ':'):
      group = cls[len(domain) + 1:]

    # Fall back to whatever is available to us
    # e.g. windows guest which only record domain name 'win7'
    else:
      group = cls

  return '{ "dt": "%s", "group": "%s", "title": "%s", "timeline": "%s" }' % (dt, group, title, CONF_timeline )

def write_data(data, now):
  filename = "qmt_" + str(to_timestamp(now)) + ".json"

  try:
    with open(join(CONF_storage_location, filename), 'w') as f:
      f.write(data)
  except Exception as e:
    log(str(e))
    return False

def forward_data(now, last_forward):
  if now - timedelta(0, CONF_forward_delay) >= last_forward:
    files = CONF_storage_location + "*"

    call(CONF_forward_cmd % files, shell = True)
    return now

  else:
    return last_forward

def local_time():
  return datetime.now(tz = localtimezone.Local)

def to_timestamp(now):
  return (now - datetime(1970, 1, 1, tzinfo = localtimezone.Local)).total_seconds()

def query_audio_playback():
  """Checks whether audio is currently playing."""
  if not CONF_no_idle_during_audio:
    return False

  try:
    # Output is trusted, using shell=True should be safe
    out = check_output("cat $(find /proc/asound/ -name status) | grep RUNNING | wc -l", shell = True)

    return int(out.replace('\0', '')) > 0
  except Exception as e:
    log(str(e))
    return False

loop()
