# Patch stuff - used for applying patch to a certain revision
import sys
import re

path_global = ''
diffs = {}

def _files(repo_path, file_path, revision):
    """Download file from repository and store it in local temporary."""

    file = tempfile.mktemp()
    output = open(file, 'w+')
    if path is not None:
        output.write(commands.getoutput('hg cat '  + " --rev " + str(revision) + " " + repo_path + file_path))
    output.close()
    return file

def _diff(repo_path, file_path, revision):
  from_file = _files(repo_path, file_path, revision)
  # How to get location of from_file so I could patch it with hunk?
  # I am aware of tempfile.NamedTemporaryFile() which might help
  # but that is available only from 2.6
  
def _parse(file_path):
  # How to get patch path on FS?
  global diffs
  key = ''
  for line in lines:
    path = changes_re.findall(line)

    if len(path):
      key = path[0]
      diffs[key] = u''
    elif len(key):
      if not line[0:4] == 'diff':
        diffs[key] += unicode(line, 'utf-8')

def _info(path, revision):
  # How do I get patch location on FS?!
  _parse(patch_path);  
  return [_diff(path, keys, revision) for 
    keys in diffs.keys()]

def info(path, revision):
    global path_global, revision_global
    path_global = path
    return _info(path, revision)

def init(instance):
    instance.registerUtil('apply_patch', info)
