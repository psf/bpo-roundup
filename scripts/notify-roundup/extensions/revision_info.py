# Subversion integration information fetcher
# 
# Extracts information about a specific revision from a local repository.
#
# Place this file in your tracker's "extensions" directory.

import sys, os, time
from svn import core, fs, delta, repos
from libsvn.fs import svn_fs_file_contents as file_contents
import tempfile
import logging

hdlr = logging.FileHandler('/tmp/log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)

def _dump_file(root, path):
    """Download file from repository and store it in local temporary."""

    file = tempfile.mktemp()
    output = open(file, 'w+')
    if path is not None:
        stream = file_contents(root, path)
        try:
            while 1:
                chunk = core.svn_stream_read(stream, core.SVN_STREAM_CHUNK_SIZE)
                if not chunk:
                    break
                output.write(chunk)
        finally:
            core.svn_stream_close(stream)
    output.close()
    return file

class ChangeSetItem:
    def __init__(self, new_root, old_root, path, change):

        self.new_root = new_root
        self.old_root = old_root
        self.path = path
        if change.path:
            self.action = change.added and 'new' or 'modified'
        else:
            self.action = 'delete'
        self.change = change

    def diff(self):
        from difflib import HtmlDiff

        from_file = _dump_file(self.old_root, self.change.path)
        to_file = _dump_file(self.new_root, self.path)
        html = HtmlDiff()
        return html.make_file(open(from_file, 'r').readlines(),
                              open(to_file, 'r').readlines(),
                              'original', 'new')

        return html_diff(file1, file2)


def _info(pool, path, rev):
    repos_ptr = repos.svn_repos_open(path, pool)
    fs_ptr = repos.svn_repos_fs(repos_ptr)

    new_root = fs.revision_root(fs_ptr, rev, pool)
    old_root = fs.revision_root(fs_ptr, rev - 1, pool)

    # get all changes
    editor = repos.RevisionChangeCollector(fs_ptr, rev, pool)
    e_ptr, e_baton = delta.make_editor(editor, pool)
    repos.svn_repos_replay(new_root, e_ptr, e_baton, pool)

    changeset = editor.changes.items()
    logging.error(changeset)
    changeset.sort()
    return [ChangeSetItem(new_root, old_root, path, change)
            for path, change in changeset]

def info(path, revision):
    return core.run_app(_info, path, int(revision))

def init(instance):
    instance.registerUtil('revision_info', info)

if __name__ == '__main__':

    path = '/home/stefan/projects/svn-roundup/repo'
    revision = 1
    if len(sys.argv) == 2:
        revision = int(sys.argv[1])
    print revision_info(path, revision)

