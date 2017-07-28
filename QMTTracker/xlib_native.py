"""
Credit: parts copied from https://github.com/BoboTiG/python-mss/blob/master/mss/linux.py
"""

# Shell exec, used for audio activity checks
from subprocess import check_output

# Calls in native X11 and Xss libariries, used in monitoring user activity, and xscreensaver locked status
import ctypes
import ctypes.util
import os

# Const
ScreenSaverOn = 1

# Xss info structure
class XScreenSaverInfo(ctypes.Structure):
  """ typedef struct { ... } XScreenSaverInfo; """
  _fields_ = [('window',      ctypes.c_ulong), # screen saver window
              ('state',       ctypes.c_int),   # off,on,disabled
              ('kind',        ctypes.c_int),   # blanked,internal,external
              ('since',       ctypes.c_ulong), # milliseconds
              ('idle',        ctypes.c_ulong), # milliseconds
              ('event_mask',  ctypes.c_ulong)] # events

# Stubs
class XWindowAttributes(ctypes.Structure):
  """XWindowAttrAttributes stub"""

class XDisplay(ctypes.Structure):
  """Display stub"""

# Core of activity tracking
class xlib_native(object):
  """Accesses idle time, screensaver locked status (through libXss).
  Note: xscreensaver is incompatible with libXss (makes sense), a custom check is implemented in xlib_python"""

  def __enter__(self):
    self.load_libraries()
    self.init_xobjects()
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.free_xobjects()

  def load_libraries(self):
    x11lib = ctypes.util.find_library('X11')
    xsslib = ctypes.util.find_library('Xss')
    
    try:
      self.xlib = ctypes.cdll.LoadLibrary(x11lib)
    except Exception as e:
      raise ModuleNotFoundError("libX11.so could not be found, make sure it is installed.")

    try:
      self.xss = ctypes.cdll.LoadLibrary(xsslib)
    except Exception as e:
      raise ModuleNotFoundError("libXss.so could not be found, make sure it is installed.")

    #xss_event_base, xss_error_base = ctypes.c_int(), ctypes.c_int()
    #have_xss = self.xss.XScreenSaverQueryExtension(
    #  self.display, ctypes.byref(xss_event_base), ctypes.byref(xss_error_base))

    #if not have_xss:
    #  raise ValueError("Xss extension is disabled.")

    self.xlib.XOpenDisplay.argtypes = [ ctypes.c_char_p ]
    self.xlib.XOpenDisplay.restype = ctypes.POINTER(XDisplay)

    self.xlib.XDefaultScreen.argtypes = [ ctypes.POINTER(XDisplay) ]
    self.xlib.XDefaultScreen.restype = ctypes.c_int

    self.xlib.XDefaultRootWindow.argtypes = [ ctypes.POINTER(XDisplay), ctypes.c_int ]
    self.xlib.XDefaultRootWindow.restype = ctypes.POINTER(XWindowAttributes)
    
    self.xss.XScreenSaverAllocInfo.restype = ctypes.POINTER(XScreenSaverInfo)
  
  def init_xobjects(self):
    self.display = self.xlib.XOpenDisplay(os.environ['DISPLAY'].encode('utf-8'))
    self.xssinfo = self.xss.XScreenSaverAllocInfo()
    self.root = self.xlib.XDefaultRootWindow(self.display, self.xlib.XDefaultScreen(self.display))

  def free_xobjects(self):
    self.xss.XFree(self.xssinfo)
    self.xss.XCloseDisplay(self.display)

  def query_screensaver_info(self):
    """Queries into native libraries to gather idle and locked status"""
    self.xss.XScreenSaverQueryInfo(self.display, self.root, self.xssinfo)

    return self.xssinfo.contents.idle, self.xssinfo.contents.state == ScreenSaverOn
