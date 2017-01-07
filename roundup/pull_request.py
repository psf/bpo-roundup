from roundup.exceptions import *

import hashlib
import hmac
import json
import re
import os
import logging


if hasattr(hmac, 'compare_digest'):
    compare_digest = hmac.compare_digest
else:
    def compare_digest(a, b):
        return a == b

url_re = re.compile(r'https://github.com/python/cpython/pull/(?P<number>\d+)')
issue_id_re = re.compile(r'bpo\s*(\d+)', re.I)

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
        Extracts github event from header field.
        """
        return self.request.headers.get('X-GitHub-Event', None)


class Event(object):
    """
    Event is base class for all GitHub events.
    """

    def __init__(self, db, data):
        self.db = db
        self.data = data

    def set_current_user(self):
        """
        Helper method used for setting current user for roundup, based
        on the information from github about event author.
        """
        github_username = self.get_github_username()
        user_id = self.db.user.filter(None, {'github': github_username})
        # TODO set bpobot as userid when none is found
        if len(user_id) == 1:
            # TODO what if multiple bpo users have the same github username?
            username = self.db.user.get(user_id[0], 'username')
            self.db.setCurrentUser(username)

    def dispatch(self):
        """
        Main method responsible for responding to incoming github event.
        """
        self.set_current_user()
        action = self.data.get('action', '').encode('utf-8')
        issue_ids = self.get_issue_ids()
        if not issue_ids:
            # no issue id found
            create_issue = os.environ.get('CREATE_ISSUE', False)
            if create_issue:
                # TODO we should fill in the issue with more details
                title = self.data.get('pull_request').get('title', '').encode('utf-8')
                issue_ids = list(self.db.issue.create(title=title))
        prid, title = self.get_pr_details()
        self.handle_action(action, prid, title, issue_ids)

    def handle_create(self, prid, title, issue_ids):
        """
        Helper method for linking GitHub pull request with an issue.
        """
        # search for an existing issue first
        issue_exists = len(self.db.issue.filter(None, {'id': issue_ids})) == len(issue_ids)
        if not issue_exists:
            return
        for issue_id in issue_ids:
            # verify if this PR is already linked
            prs = self.db.issue.get(issue_id, 'pull_requests')
            if set(prs).intersection(self.db.pull_request.filter(None, {'number': prid})):
                continue
            # create a new link
            if title:
                newpr = self.db.pull_request.create(number=prid, title=title)
            else:
                newpr = self.db.pull_request.create(number=prid)
            prs.append(newpr)
            self.db.issue.set(issue_id, pull_requests=prs)
            self.db.commit()

    def handle_update(self, prid, title, issue_ids):
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
                    if probj.number == prid and probj.title != title:
                        self.db.pull_request.set(probj.id, title=title)
                        self.db.commit()
            else:
                self.handle_create(prid, title, [issue_id])

    def handle_action(self, action, prid, title, issue_ids):
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

    def handle_action(self, action, prid, title, issue_ids):
        if action in ('opened', 'created'):
            self.handle_create(prid, title, issue_ids)
        elif action == 'edited':
            self.handle_update(prid, title, issue_ids)

    def get_issue_ids(self):
        """
        Extract issue IDs from pull request comments.
        """
        pull_request = self.data.get('pull_request')
        if pull_request is None:
            raise Reject()
        title = pull_request.get('title', '').encode('utf-8')
        body = pull_request.get('body', '').encode('utf-8')
        return list(set(issue_id_re.findall(title) + issue_id_re.findall(body)))

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
        title = pull_request.get('title', '').encode('utf-8')
        return str(number), title

    def get_github_username(self):
        """
        Extract github username from a pull request.
        """
        pull_request = self.data.get('pull_request')
        if pull_request is None:
            raise Reject()
        return pull_request.get('user', {}).get('login', '').encode('utf-8')

class IssueComment(Event):
    """
    Class responsible for handling issue comment events, but only within the
    scope of a pull request, for now.
    """

    def __init__(self, db, data):
        super(IssueComment, self).__init__(db, data)

    def handle_action(self, action, prid, title, issue_ids):
        if action in ('created', 'edited'):
            self.handle_create(prid, title, issue_ids)

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
        title = issue.get('title', '').encode('utf-8')
        body = comment.get('body', '').encode('utf-8')
        return list(set(issue_id_re.findall(title) + issue_id_re.findall(body)))

    def get_pr_details(self):
        """
        Extract pull request number and title.
        """
        issue = self.data.get('issue')
        if issue is None:
            raise Reject()
        url = issue.get('pull_request', {}).get('html_url')
        number_match = url_re.search(url)
        if not number_match:
            return (None, None)
        return number_match.group('number'), None

    def get_github_username(self):
        """
        Extract github username from a comment.
        """
        issue = self.data.get('issue')
        if issue is None:
            raise Reject()
        return issue.get('user', {}).get('login', '').encode('utf-8')
