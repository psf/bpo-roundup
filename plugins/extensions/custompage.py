# This Roundup extension was written by techtonik@gmail.com and it's been
# placed in the Public Domain. Copy and modify to your heart's content.

"""
The extension demonstrates Roundup API for creating custom pages
for tracker. 
"""


def render_html():
  """Page with static html."""
  return "I'm <b>glowing</b>."

def render_version():
  """
  Page with some 'dynamic' content demonstrating that extension
  doesn't may import Roundup to access its API, but doesn't need
  to depend on it.
  """
  import roundup
  return "Roundup %s" % roundup.__version__


def init(tracker):
  tracker.registerHandler('/staticpage', render_html)
  tracker.registerHandler('/version', render_version)
