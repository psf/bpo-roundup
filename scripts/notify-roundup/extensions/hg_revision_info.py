import commands
from difflib import HtmlDiff    
import tempfile

path_global = '/home/mario/TestInstances/hgrepo'

def _dump_file(path, revision):
    """Download file from repository and store it in local temporary."""

    file = tempfile.mktemp()
    file2 = tempfile.mktemp()
    output = open(file, 'w+')
    output2 = open(file2, 'w+')
    if path is not None:
        output.write(commands.getoutput('hg cat '  + " --rev " + str(revision) + " " + path))
        output2.write(commands.getoutput('hg cat ' + " --rev " + str(revision-1) + " " + path))
    output.close()
    output2.close()
    return file, file2

class ChangeSetItem:
    def __init__(self,line):

        pathos = line.split()
        self.path = pathos[1]

        self.line = line
        
        check = line.find('+')
        if check != -1:
            self.action = 'added'
        check = line.find('!')
        if check != -1:
            self.action = 'modified'
        check = line.find('-')
        if check != -1:
            self.action = 'removed'    

        self.change = 'test'
        
    def diff(self):
        from difflib import HtmlDiff

        from_file, to_file = _dump_file(path_global, -1)
        html = HtmlDiff()
        return html.make_file(open(from_file, 'r').readlines(),
                              open(to_file, 'r').readlines(),
                              'original', 'new')

        return html_diff(file1, file2)
    
    
def _info(path, revision):

    changes = commands.getoutput("hg log -p -r " + revision + " " + path + " | lsdiff -s --strip=1")
    line_changes = changes.splitlines()
    return [ChangeSetItem(line) for 
        line in line_changes]
    


def info(path, revision):
    global path_global
    path_global = path
    return _info(path, revision)
    

def init(instance):
    instance.registerUtil('revision_info', info)

