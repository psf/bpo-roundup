# Subversion integration auditor
# 
# Watches for messages formatted by the notify-roundup.py Subversion hook
# script, and parses the meta-data out of them, removing it from the
# message body in the process.
#
# Place this file in your tracker's "detectors" directory.
#
# See end of file for change history

import re, sets

import roundup.date

import ConfigParser

svn_msg = re.compile('^(revision|repos|host|date|summary)=(.*)$')
ini_path = '/path/to/notify-roundup.ini'

def parse_message(db, cl, nodeid, newvalues):
    '''Parse an incoming message for Subversion information.
    '''

    # collect up our meta-data from the message
    info = {}
    content = []
    for line in newvalues.get('content', '').splitlines():
        m = svn_msg.match(line)
        if not m:
            content.append(line)
            continue
        info[m.group(1)] = m.group(2).strip()

    # only continue if all five pieces of information are present
    if len(info) != 5:
        return

    # look up the repository id
    try:
        svn_repo_id = db.svn_repo.stringFind(path=info['repos'],
            host=info['host'])[0]
    except IndexError:
        #logger.error('no repository %s in tracker'%repos.repos_dir)
        return

    # create the subversion revision item
    svn_rev_id = db.svn_rev.create(repository=svn_repo_id,
        revision=int(info['revision']))

    # minor bit of content cleaning - remove the single leading blank line
    if content and not content[0].strip():
        del content[0]

    # set the info on the message
    newvalues['content'] = '\n'.join(content)
    newvalues['date'] = roundup.date.Date(info['date'])
    newvalues['summary'] = info['summary']
    newvalues['revision'] = svn_rev_id

def undo_title(db, cl, nodeid, newvalues):
    '''Don't change the title of issues to "SVN commit message..."'''
    if newvalues.get('title', '').lower().startswith('svn commit message'):
        del newvalues['title']


def init(db):
    db.msg.audit('create', parse_message)
    cfg = ConfigParser.ConfigParser()
    cfg.read(ini_path)
    fetch_klass = cfg.get('main', 'item-class')
    klass = db.getclass(fetch_klass)
    klass.audit('set', undo_title)


