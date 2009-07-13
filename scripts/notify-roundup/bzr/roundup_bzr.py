from bzrlib import branch
import commands
import os


# Installation:
# Copy this file to ~/.bazaar/plugins

notify_path = /path/to/your/notify-roundup.py
config_path = /path/to/your/notify-roundup.ini
roundup_instance_path = /path/to/your/roundup/instance

def post_commit_hook(branch='.'):
    my_branch = Branch.open(branch)
    revision = my_branch.last_revision()
    repo_dir = commands.getoutput('pwd')
    os.system("PYTHONPATH=" + roundup_instance_path + " " + "/usr/bin/python" + notify_path + config_path + " " + repo_dir + " " +  revision)
    

branch.Branch.hooks.install_named_hook('post_commit', post_commit_hook,
                                 'Bazaar -> Roundup integration hook')

