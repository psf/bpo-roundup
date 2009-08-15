# Patch stuff - used for applying patch to a certain revision

path_global = ''

def _files(path, revision):
    """Download file from repository and store it in local temporary."""

    file = tempfile.mktemp()
    output = open(file, 'w+')
    if path is not None:
        output.write(commands.getoutput('hg cat '  + " --rev " + str(revision) + " " + path))
    output.close()
    return file
    
def info(path, revision):
    global path_global
    path_global = path
    return _info(path, revision)

def init(instance):
    instance.registerUtil('apply_patch', info)
