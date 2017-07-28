"""
Credit: parts copied or inspired from
python-xlib @ https://github.com/python-xlib/python-xlib/blob/master/Xlib/xobject/drawable.py
Erik @ https://github.com/ActivityWatch/aw-watcher-window/blob/master/aw_watcher_window/xlib.py
Chromium @ https://chromium.googlesource.com/chromium/src/+/a033e0202b133bb5892e2e28ca37bf052afad816/ui/base/idle/screensaver_window_finder_x11.cc
"""

import Xlib
import Xlib.display

# Const
_PROP_WM_CLASS = 'WM_CLS'
_PROP_WM_NAME = 'WM_NAME'
_PROP_WM_MACHINE = 'WM_MACHINE'
_PROP_DOMU_DOMAIN = 574 #574: 'sys-net'
_PROP_DOMU_TITLE1 = 37 #37: 'user@sys-net:~'
_PROP_DOMU_TITLE2 = 39 #39: 'user@sys-net:~'

_ATOM_LOCK = 'LOCK'
_ATOM_SCREENSAVER_STATUS = '_SCREENSAVER_STATUS'
_ATOM_ACTIVE_WINDOW = '_NET_ACTIVE_WINDOW'

_STRING_ENCODING = 'ISO-8859-1'
_UTF8_STRING_ENCODING = 'UTF-8'

# Core class
class xlib_python(object):
  """Tracks active x11 windows using python-xlib"""
  def __init__(self):
    self.display = Xlib.display.Display()
    self.screen = self.display.screen()

  def get_xscreensaver_status(self):
    """Checks whether xscreensaver is active or not"""
    atom_lock = self.display.get_atom(_ATOM_LOCK)
    atom_ss_status = self.display.get_atom(_ATOM_SCREENSAVER_STATUS)

    prop = self.screen.root.get_full_property(atom_ss_status, Xlib.X.AnyPropertyType)

    if not prop or not prop.value:
      # Log ?
      return False

    return prop.value[0] == atom_lock

  def get_active_window_id(self):
    atom = self.display.get_atom(_ATOM_ACTIVE_WINDOW)
    prop = self.screen.root.get_full_property(atom, Xlib.X.AnyPropertyType)

    if not prop:
      return None
    
    return prop.value[-1] if prop.value[-1] != 0 else prop.value[0]

  def get_window_object(self, window_id):
    return self.display.create_resource_object('window', window_id)

  @staticmethod
  def get_text_property(window, prop_id):
    prop = window.get_full_property(prop_id, Xlib.X.AnyPropertyType, 255)

    if not prop or prop.format != 8:
      return None

    if prop.property_type == Xlib.Xatom.STRING:
      return prop.value.decode(_STRING_ENCODING)
    
    if prop.property_type == window.display.get_atom('UTF8_STRING'):
      return prop.value.decode(_UTF8_STRING_ENCODING)

    return prop.value


  @staticmethod
  def get_window_properties(window):
    while window:
      cls = window.get_wm_class()

      if not cls:
        window = window.query_tree().parent

      else:
        break

    dict = {}
    dict[_PROP_WM_CLASS] = cls[0] if cls else ""
    dict[_PROP_WM_NAME] = window.get_wm_name()
    dict[_PROP_WM_MACHINE] = window.get_wm_client_machine()
    dict[_PROP_DOMU_DOMAIN] = xlib_python.get_text_property(window, _PROP_DOMU_DOMAIN)
    dict[_PROP_DOMU_TITLE2] = xlib_python.get_text_property(window, _PROP_DOMU_TITLE2)

    return dict

  def get_active_window(self):
    """Builds a dictionary with active windows's properties"""
    window_id = self.get_active_window_id()

    if not window_id:
      return None

    window = self.get_window_object(window_id)
    window_props = self.get_window_properties(window)

    return window_props


