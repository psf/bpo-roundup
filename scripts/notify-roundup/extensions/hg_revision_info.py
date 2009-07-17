import commands
from difflib import HtmlDiff    

path = '/home/mario/TestInstances/hgrepo'

def _dump_files(path, revision):
    """Download file from repository and store it in local temporary."""

    file = tempfile.mktemp()
    file2 = tempfile.mktemp()
    output = open(file, 'w+')
    output2 = open(file2, 'w+')
    if path is not None:
        output.write(commands.getoutput('hg cat '  + " --rev " + revision + " " + path))
        output2.write(commands.getoutput('hg cat ' + " --rev " + int(revision-1) + " " + path))
    output.close()
    output2.close()
    return file, file2

class ChangeSetItem:
    def __init__(self, path, change):

        self.path = path
        #if change.path:
            self.action = change.added and 'new' or 'modified'
        #else:
        #    self.action = 'delete'
        self.change = change

    def diff(self):
        from difflib import HtmlDiff

        from_file, to_file = _dump_file(path, -1)
        html = HtmlDiff()
        return html.make_file(open(from_file, 'r').readlines(),
                              open(to_file, 'r').readlines(),
                              'original', 'new')

        return html_diff(file1, file2)
    
    
def info(path, revision):
    dict = {}

    changes = commands.getoutput("hg log -p -r " + revision + " " + path + " | lsdiff -s --strip=1")
    line_changes = changes.splitlines()
    for line in line_changes:
        check = line.str('+')
        if check != -1:
            split_check = line.split()
            dict['Added:'] = split_check[1]
            diff(split_check[1], revision)
            continue
        check = line.str('-')
        if check != -1:
            split_check = line.split()
            dict['Removed:'] = split_check[1]
            continue
        check = line.str('!')
        if check != -1:
            split_check = line.split()
            dict['Modified:'] = split_check[1]    
            continue    
def info(path, revision):
    return _info(path, int(revision))
    

def init(instance):
    instance.registerUtil('revision_info', info)
