import commands
from difflib import HtmlDiff    

def _dump_files(path, revision):
    """Download file from repository and store it in local temporary."""

    file = tempfile.mktemp()
    file2 = tempfile.mktemp()
    output = open(file, 'w+')
    output2 = open(file2, 'w+')
    if path is not None:
        output.write(commands.getoutput('hg cat '  + " --rev " + revision + " " + path))
        output2.write(commands.getoutput('hg cat ' + " --rev " + revision-1 + " " + path))
    output.close()
    output2.close()
    return file, file2

def diff (path, revision):
    """ Diff between two revisions."""
    
    
def info(path, revision):
    dict = {}

    changes = commands.getoutput("hg log -p -r " + revision + " " + path + " | lsdiff -s --strip=1")
    return changes
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
        
    

def init(instance):
    instance.registerUtil('revision_info', info)
