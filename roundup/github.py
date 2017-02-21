import hashlib
import hmac
import json
import re
import os
import logging

from roundup.date import Date
from roundup.exceptions import Unauthorised, MethodNotAllowed, \
    UnsupportedMediaType, Reject

if hasattr(hmac, 'compare_digest'):
    compare_digest = hmac.compare_digest
else:
    def compare_digest(a, b):
        return a == b

URL_RE = re.compile(r'https://github.com/python/cpython/pull/(?P<number>\d+)')
VERBS = r'(?:\b(?P<verb>close[sd]?|closing|)\s+)?'
ISSUE_RE = re.compile(r'%sbpo-(?P<issue_id>\d+)' % VERBS, re.I|re.U)
BRANCH_RE = re.compile(r'(2\.\d|3\.\d|master)', re.I)

COMMENT_TEMPLATE = u"""\
New changeset {changeset_id} by {author} in branch '{branch}':
{commit_msg}
{changeset_url}
"""

class GitHubHandler:
    """
    GitHubHandler is responsible for parsing and serving all events coming
    from GitHub. Details about GitHub webhooks can be found at:
    https://developer.github.com/webhooks/
    """

    def __init__(self, client):
        self.db = client.db
        self.request = client.request
        self.form = client.form
        self.env = client.env

    def dispatch(self):
        try:
            self.verify_request()
            self.validate_webhook_secret()
            self.extract()
        except (Unauthorised, MethodNotAllowed,
                UnsupportedMediaType, Reject) as err:
            raise
        except Exception as err:
            logging.error(err, exc_info=True)
            raise Reject()

    def extract(self):
        """
        This method is responsible for extracting information from GitHub event
        and decide what to do with it more. Currently it knows how to handle
        pull requests and comments.
        """
        event = self.get_event()
        # we're only handling PR-related events, all others just return OK, but
        # no action is being performed on the bpo side
        if event in ('pull_request', 'pull_request_review_comment'):
            data = json.loads(self.form.value)
            handler = PullRequest(self.db, data)
            handler.dispatch()
        elif event == 'issue_comment':
            data = json.loads(self.form.value)
            handler = IssueComment(self.db, data)
            handler.dispatch()
        elif event == 'push':
            data = json.loads(self.form.value)
            handler = Push(self.db, data)
            handler.dispatch()

    def validate_webhook_secret(self):
        """
        Validates request signature against SECRET_KEY environment variable.
        This verification is based on HMAC hex digest calculated from the sent
        payload. The value of SECRET_KEY should be exactly the same as the one
        configured in GitHub webhook secret field.
        """
        key = os.environ.get('SECRET_KEY')
        if key is None:
            logging.error('Missing SECRET_KEY environment variable set!')
            raise Reject()
        data = str(self.form.value)
        signature = 'sha1=' + hmac.new(key, data,
                                       hashlib.sha1).hexdigest()
        header_signature = self.request.headers.get('X-Hub-Signature', '')
        if not compare_digest(signature, header_signature):
            raise Unauthorised()

    def verify_request(self):
        """
        Verifies if request contains expected method, content type and event.
        """
        method = self.env.get('REQUEST_METHOD', None)
        if method != 'POST':
            raise MethodNotAllowed()
        content_type = self.env.get('CONTENT_TYPE', None)
        if content_type != 'application/json':
            raise UnsupportedMediaType()
        if self.get_event() is None:
            raise Reject()

    def get_event(self):
        """
        Extracts GitHub event from header field.
        """
        return self.request.headers.get('X-GitHub-Event', None)


class Event(object):
    """
    Event is base class for all GitHub events.
    """

    def __init__(self, db, data):
        self.db = db
        self.data = data

    def set_roundup_user(self):
        """
        Helper method used for setting the current user for Roundup, based
        on the information from GitHub about event author.
        """
        github_username = self.get_github_username()
        user_ids = self.db.user.filter(None, {'github': github_username})
        if not user_ids:
            # set bpobot as userid when none is found
            user_ids = self.db.user.filter(None, {'username': 'python-dev'})
            if not user_ids:
                # python-dev does not exists, anonymous will be used instead
                return
        username = self.db.user.get(user_ids[0], 'username')
        self.db.setCurrentUser(username)

    def dispatch(self):
        """
        Main method responsible for responding to incoming GitHub event.
        """
        self.set_roundup_user()
        action = self.data.get('action', '')
        issue_ids = self.get_issue_ids()
        if not issue_ids:
            # no issue id found
            create_issue = os.environ.get('CREATE_ISSUE', False)
            if create_issue:
                # TODO we should fill in the issue with more details
                title = self.data.get('pull_request', {}).get('title', '')
                issue_ids = list(self.db.issue.create(
                    title=title.encode('utf-8')))
        prid, title, status = self.get_pr_details()
        self.handle_action(action, prid, title, status, issue_ids)

    def handle_create(self, prid, title, status, issue_ids):
        """
        Helper method for linking GitHub pull request with an issue.
        """
        # search for an existing issue first
        issue_exists = len(self.db.issue.filter(None, {'id': issue_ids})) == len(issue_ids)
        if not issue_exists:
            return
        for issue_id in issue_ids:
            id = issue_id.encode('utf-8')
            # verify if this PR is already linked
            prs = self.db.issue.get(id, 'pull_requests')
            if set(prs).intersection(self.db.pull_request.filter(None, {'number': prid})):
                continue
            # create a new link
            if not title:
                title = ""
            if not status:
                status = ""
            newpr = self.db.pull_request.create(number=prid,
                title=title.encode('utf-8'), status=status.encode('utf-8'))
            prs.append(newpr)
            self.db.issue.set(id, pull_requests=prs)
            self.db.commit()

    def handle_update(self, prid, title, status, issue_ids):
        """
        Helper method for updating GitHub pull request.
        """
        # update handles only title changes, for now
        if not title:
            return
        # search for an existing issue first
        issue_exists = len(self.db.issue.filter(None, {'id': issue_ids})) == len(issue_ids)
        if not issue_exists:
            return
        for issue_id in issue_ids:
            # verify if this PR is already linked
            prs = self.db.issue.get(issue_id, 'pull_requests')
            if set(prs).intersection(self.db.pull_request.filter(None, {'number': prid})):
                for pr in prs:
                    probj = self.db.pull_request.getnode(pr)
                    # check if the number match and title did change, and only then update
                    if probj.number == prid:
                        self.db.pull_request.set(probj.id, title=title, status=status)
                        self.db.commit()
            else:
                self.handle_create(prid, title, status, [issue_id])

    def handle_action(self, action, prid, title, status, issue_ids):
        raise NotImplementedError

    def get_github_username(self):
        raise NotImplementedError

    def get_issue_ids(self):
        raise NotImplementedError

    def get_pr_details(self):
        raise NotImplementedError


class PullRequest(Event):
    """
    Class responsible for handling pull request events.
    """

    def __init__(self, db, data):
        super(PullRequest, self).__init__(db, data)

    def handle_action(self, action, prid, title, status, issue_ids):
        if action in ('opened', 'created'):
            self.handle_create(prid, title, status, issue_ids)
        elif action in ('edited', 'closed'):
            self.handle_update(prid, title, status, issue_ids)

    def get_issue_ids(self):
        """
        Extract issue IDs from pull request comments.
        """
        pull_request = self.data.get('pull_request')
        if pull_request is None:
            raise Reject()
        title = pull_request.get('title', '')
        body = pull_request.get('body', '')
        title_ids = [x[1] for x in ISSUE_RE.findall(title)]
        body_ids = [x[1] for x in ISSUE_RE.findall(body)]
        return list(set(title_ids + body_ids))

    def get_pr_details(self):
        """
        Extract pull request number and title.
        """
        pull_request = self.data.get('pull_request')
        if pull_request is None:
            raise Reject()
        number = pull_request.get('number', None)
        if number is None:
            raise Reject()
        title = pull_request.get('title', '')
        status = pull_request.get('state', '')
        # GitHub has two states open and closed, information about pull request
        # being merged in kept in separate field
        if pull_request.get('merged', False):
            status = "merged"
        return str(number), title, status

    def get_github_username(self):
        """
        Extract GitHub username from a pull request.
        """
        pull_request = self.data.get('pull_request')
        if pull_request is None:
            raise Reject()
        return pull_request.get('user', {}).get('login', '')


class IssueComment(Event):
    """
    Class responsible for handling issue comment events, but only within the
    scope of a pull request, for now.
    """

    def __init__(self, db, data):
        super(IssueComment, self).__init__(db, data)

    def handle_action(self, action, prid, title, status, issue_ids):
        if action in ('created', 'edited'):
            self.handle_create(prid, title, status, issue_ids)

    def get_issue_ids(self):
        """
        Extract issue IDs from comments.
        """
        issue = self.data.get('issue')
        if issue is None:
            raise Reject()
        comment = self.data.get('comment')
        if comment is None:
            raise Reject()
        title = issue.get('title', '')
        body = comment.get('body', '')
        title_ids = [x[1] for x in ISSUE_RE.findall(title)]
        body_ids = [x[1] for x in ISSUE_RE.findall(body)]
        return list(set(title_ids + body_ids))

    def get_pr_details(self):
        """
        Extract pull request number and title.
        """
        issue = self.data.get('issue')
        if issue is None:
            raise Reject()
        url = issue.get('pull_request', {}).get('html_url')
        number_match = URL_RE.search(url)
        if not number_match:
            return (None, None, None)
        return number_match.group('number'), None, None

    def get_github_username(self):
        """
        Extract GitHub username from a comment.
        """
        issue = self.data.get('issue')
        if issue is None:
            raise Reject()
        return issue.get('user', {}).get('login', '')


class Push(Event):
    """
    Class responsible for handling push events.
    """

    def get_github_username(self):
        """
        Extract GitHub username from a push event.
        """
        return self.data.get('pusher', []).get('name', '')

    def dispatch(self):
        """
        Main method responsible for responding to incoming GitHub event.
        """
        self.set_roundup_user()
        commits = self.data.get('commits', [])
        ref = self.data.get('ref', 'refs/heads/master')
        # messages dictionary maps issue number to a tuple containing
        # the message to be posted as a comment an boolean flag informing
        # if the issue should be 'closed'
        messages = {}
        # extract commit messages
        for commit in commits:
            msgs = self.handle_action(commit, ref)
            for issue_id, (msg, close) in msgs.iteritems():
                if issue_id not in messages:
                    messages[issue_id] = (u'', False)
                curr_msg, curr_close = messages[issue_id]
                # we append the new message to the other and do binary OR
                # on close, so that at least one information will actually
                # close the issue
                messages[issue_id] = (curr_msg + u'\n' + msg, curr_close or close)
        if not messages:
            return
        for issue_id, (msg, close) in messages.iteritems():
            # add comments to appropriate issues...
            id = issue_id.encode('utf-8')
            try:
                issue_msgs = self.db.issue.get(id, 'messages')
            except IndexError:
                # See meta issue #613: the commit message might also include
                # PR ids that shouldn't be included.
                continue
            newmsg = self.db.msg.create(content=msg.encode('utf-8'),
                author=self.db.getuid(), date=Date('.'))
            issue_msgs.append(newmsg)
            # ... and close, if needed
            if close:
                self.db.issue.set(id,
                    messages=issue_msgs,
                    status=self.db.status.lookup('closed'),
                    resolution=self.db.resolution.lookup('fixed'),
                    stage=self.db.stage.lookup('resolved'))
            else:
                self.db.issue.set(id, messages=issue_msgs)
        self.db.commit()

    def handle_action(self, commit, ref):
        """
        This is implementing the same logic as the mercurial hook from here:
        https://hg.python.org/hooks/file/tip/hgroundup.py
        """
        branch = ref.split('/')[-1]
        if not BRANCH_RE.match(branch):
            return dict()
        description = commit.get('message', '')
        matches = ISSUE_RE.finditer(description)
        messages = {}
        for match in matches:
            data = match.groupdict()
            # check for duplicated issue numbers in the same commit msg
            if data['issue_id'] in messages:
                continue
            close = bool(data.get('verb'))
            messages[data['issue_id']] = (COMMENT_TEMPLATE.format(
                author=commit.get('committer', {}).get('name', ''),
                branch=branch,
                changeset_id=commit.get('id', ''),
                changeset_url=commit.get('url', ''),
                commit_msg=description.splitlines()[0],
            ), close)
        return messages
