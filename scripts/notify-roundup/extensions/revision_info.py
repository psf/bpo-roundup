# Subversion integration information fetcher
# 
# Extracts information about a specific revision from a local repository.
#
# Place this file in your tracker's "extensions" directory.

import sys, os, time
from svn import core, fs, delta, repos

def inner(pool, path, rev):
    repos_ptr = repos.svn_repos_open(path, pool)
    fs_ptr = repos.svn_repos_fs(repos_ptr)

    root = fs.revision_root(fs_ptr, rev, pool)
    base_rev = rev - 1

    # get all changes
    editor = repos.RevisionChangeCollector(fs_ptr, rev, pool)
    e_ptr, e_baton = delta.make_editor(editor, pool)
    repos.svn_repos_replay(root, e_ptr, e_baton, pool)

    changelist = editor.changes.items()
    changelist.sort()

    base_root = fs.revision_root(fs_ptr, base_rev, pool)

    l = []
    for filepath, change in changelist:
        d = {'path': filepath, 'info': ''}
        if change.path:
            if change.added:
                d['action'] = 'new'
            else:
                d['action'] = 'modify'
                differ = fs.FileDiff(base_root, change.path, root, filepath,
                    pool, '-L \t(original) -L \t(new) -u'.split(' '))
                d['info'] = differ.get_pipe().read()
        else:
            d['action'] = 'delete'
        l.append(d)
    return l


def getRevisionInfo(revision):
    #path = '/Users/richard/tmp/test_repo'
    #rev = 2
    return core.run_app(inner, str(revision['repository']['path']),
        int(revision['revision']))

def init(instance):
    instance.registerUtil('getRevisionInfo', getRevisionInfo)

if __name__ == '__main__':
    print getRevision(1)

