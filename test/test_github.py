import unittest
import os
import db_test_base
import cgi
from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO
from roundup.cgi import client
from roundup.backends import list_backends
from roundup.date import Date
from roundup.github import GitHubHandler
from roundup.exceptions import *

NEEDS_INSTANCE = 1


class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, filename):
        path = os.path.dirname(os.path.abspath(__file__)) + "/data/" + filename
        request_file = open(path, 'r')
        request_text = request_file.read()
        request_file.close()
        self.rfile = StringIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()


class TestCase(unittest.TestCase):

    backend = None

    def setUp(self):
        # instance
        self.dirname = '_test_pull_request'
        self.instance = db_test_base.setupTracker(self.dirname, self.backend)
        self.env = {
            'PATH_INFO': 'http://localhost/pull_request',
            'HTTP_HOST': 'localhost',
            'TRACKER_NAME': 'test',
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': 'application/json'
        }
        os.environ['SECRET_KEY'] = "abcd"
        os.environ['CREATE_ISSUE'] = 'yes'

    def _make_client(self, filename):
        request = HTTPRequest(filename)
        form = cgi.FieldStorage(fp=request.rfile, environ=self.env,
                                headers=request.headers)
        dummy_client = client.Client(self.instance, request, self.env, form)
        dummy_client.opendb("anonymous")
        self.db = dummy_client.db
        self.db.issue.create(title="Issue 1")
        return dummy_client

    def testMissingSecretKey(self):
        os.environ.pop('SECRET_KEY')
        dummy_client = self._make_client("pingevent.txt")
        with self.assertRaises(Reject) as context:
            handler = GitHubHandler(dummy_client)
            handler.dispatch()

    def testMissingGitHubEventHeader(self):
        dummy_client = self._make_client("no-github-event-header.txt")
        with self.assertRaises(Reject) as context:
            handler = GitHubHandler(dummy_client)
            handler.dispatch()

    def testNonJSONRequestBody(self):
        dummy_client = self._make_client("non-json-body.txt")
        with self.assertRaises(Reject) as context:
            handler = GitHubHandler(dummy_client)
            handler.dispatch()

    def testSecretKey(self):
        os.environ['SECRET_KEY'] = "1234"
        dummy_client = self._make_client("pingevent.txt")
        with self.assertRaises(Unauthorised) as context:
            handler = GitHubHandler(dummy_client)
            handler.dispatch()

    def testUnsupportedMediaType(self):
        dummy_client = self._make_client("pingevent.txt")
        dummy_client.env['CONTENT_TYPE'] = 'application/xml'
        with self.assertRaises(UnsupportedMediaType) as context:
            handler = GitHubHandler(dummy_client)
            handler.dispatch()

    def testMethodNotAllowed(self):
        dummy_client = self._make_client("pingevent.txt")
        dummy_client.env['REQUEST_METHOD'] = 'GET'
        with self.assertRaises(MethodNotAllowed) as context:
            handler = GitHubHandler(dummy_client)
            handler.dispatch()

    def testPingEvent(self):
        dummy_client = self._make_client("pingevent.txt")
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        prs = self.db.issue.get('1', 'pull_requests')
        self.assertTrue(len(prs) == 0)

    def testIssueCommentEvent(self):
        dummy_client = self._make_client("issuecommentevent.txt")
        self.db.user.create(username="anish.shah", github="AnishShah")
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        prs = self.db.issue.get('1', 'pull_requests')
        self.assertEqual(len(prs), 1)
        number = self.db.pull_request.get(prs[0], 'number')
        self.assertEqual(number, '1')
        user_id = self.db.pull_request.get(prs[0], 'creator')
        self.assertEqual(self.db.user.get(user_id, 'github'), 'AnishShah')

    def testPullRequestCommentEvent(self):
        dummy_client = self._make_client("pullrequestcommentevent.txt")
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        prs = self.db.issue.get('1', 'pull_requests')
        self.assertEqual(len(prs), 1)
        number = self.db.pull_request.get(prs[0], 'number')
        self.assertEqual(number, '4')
        user_id = self.db.pull_request.get(prs[0], 'creator')
        self.assertEqual(self.db.user.get(user_id, 'username'), 'anonymous')

    def testPullRequestEventMalformed1(self):
        # empty body
        dummy_client = self._make_client("pullrequestmalformed1.txt")
        with self.assertRaises(Reject) as context:
            handler = GitHubHandler(dummy_client)
            handler.dispatch()

    def testPullRequestEventMalformed2(self):
        # missing pull_request element
        dummy_client = self._make_client("pullrequestmalformed2.txt")
        with self.assertRaises(Reject) as context:
            handler = GitHubHandler(dummy_client)
            handler.dispatch()

    def testPullRequestEventMalformed3(self):
        # missing pull_request element
        dummy_client = self._make_client("pullrequestmalformed3.txt")
        with self.assertRaises(Reject) as context:
            handler = GitHubHandler(dummy_client)
            handler.dispatch()

    def testPullRequestEventForTitle(self):
        # When the title of a PR has string "bpo-123"
        dummy_client = self._make_client("pullrequestevent.txt")
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        prs = self.db.issue.get('1', 'pull_requests')
        self.assertEqual(len(prs), 1)
        number = self.db.pull_request.get(prs[0], 'number')
        self.assertEqual(number, '11')
        user_id = self.db.pull_request.get(prs[0], 'creator')
        self.assertEqual(self.db.user.get(user_id, 'username'), 'anonymous')

    def testPullRequestEventForBody(self):
        # When the body of a PR has string "bpo-123"
        dummy_client = self._make_client("pullrequestevent1.txt")
        self.db.user.create(username="anish.shah", github="AnishShah")
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        prs = self.db.issue.get('1', 'pull_requests')
        self.assertEqual(len(prs), 1)
        number = self.db.pull_request.get(prs[0], 'number')
        self.assertEqual(number, '3')
        title = self.db.pull_request.get(prs[0], 'title')
        self.assertEqual(title, 'Created using GitHub API')
        user_id = self.db.pull_request.get(prs[0], 'creator')
        self.assertEqual(self.db.user.get(user_id, 'github'), 'AnishShah')
        status = self.db.pull_request.get(prs[0], 'status')
        self.assertEqual(status, "open")

    def testPullRequestEventForUsername(self):
        # Make sure that only a exact github username match
        dummy_client = self._make_client("pullrequestevent.txt")
        self.db.user.create(username="foo", github="_python")
        self.db.user.create(username="bar", github="a_python")
        self.db.user.create(username="baz", github="python2")
        self.db.user.create(username="expected", github="python")
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        prs = self.db.issue.get('1', 'pull_requests')
        user_id = self.db.pull_request.get(prs[0], 'creator')
        self.assertEqual(self.db.user.get(user_id, 'username'), 'expected')

    def testPullRequestEventForUsernameWithNoMatchUsesPythonDev(self):
        # Make sure that python-dev is picked if there are no matches
        dummy_client = self._make_client("pullrequestevent.txt")
        self.db.user.create(username="foo", github="_python")
        self.db.user.create(username="bar", github="a_python")
        self.db.user.create(username="python-dev", github="python2")
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        prs = self.db.issue.get('1', 'pull_requests')
        user_id = self.db.pull_request.get(prs[0], 'creator')
        self.assertEqual(self.db.user.get(user_id, 'username'), 'python-dev')

    def testPullRequestEventForUsernameWithNoMatchUsesAnonymous(self):
        # Make sure that anonymous is picked with no match and no python-dev
        dummy_client = self._make_client("pullrequestevent.txt")
        self.db.user.create(username="foo", github="_python")
        self.db.user.create(username="bar", github="a_python")
        self.db.user.create(username="baz", github="python2")
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        prs = self.db.issue.get('1', 'pull_requests')
        user_id = self.db.pull_request.get(prs[0], 'creator')
        self.assertEqual(self.db.user.get(user_id, 'username'), 'anonymous')

    def testPullRequestEventForMultipleIssueReferenceInTitle(self):
        dummy_client = self._make_client("pullrequestevent3.txt")
        self.db.issue.create(title="Issue 2")
        self.db.issue.create(title="Issue 3")
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        for i in range(1, 4):
            prs = self.db.issue.get(str(i), 'pull_requests')
            self.assertEqual(len(prs), 1)
            number = self.db.pull_request.get(prs[0], 'number')
            self.assertEqual(number, '13')
            title = self.db.pull_request.get(prs[0], 'title')
            self.assertEqual(title, 'fixes bpo-1, bpo-2, bpo-3')

    def testPullRequestEventForMultipleIssueReferenceInBody(self):
        dummy_client = self._make_client("pullrequestevent4.txt")
        self.db.issue.create(title="Issue 2")
        self.db.issue.create(title="Issue 3")
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        for i in range(1, 4):
            prs = self.db.issue.get(str(i), 'pull_requests')
            self.assertEqual(len(prs), 1)
            number = self.db.pull_request.get(prs[0], 'number')
            self.assertEqual(number, '14')
            title = self.db.pull_request.get(prs[0], 'title')
            self.assertEqual(title, 'update .gitignore')

    def testPullRequestEventForMultipleIssueReferenceInBodyAndTitle(self):
        # When both title and body of a PR has multiple and duplicated "bpo-123"
        dummy_client = self._make_client("pullrequestevent5.txt")
        self.db.issue.create(title="Issue 2")
        self.db.issue.create(title="Issue 3")
        self.db.issue.create(title="Issue 4")
        self.db.issue.create(title="Issue 5")
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        for i in range(1, 6):
            prs = self.db.issue.get(str(i), 'pull_requests')
            self.assertEqual(len(prs), 1)
            number = self.db.pull_request.get(prs[0], 'number')
            self.assertEqual(number, '11')
            title = self.db.pull_request.get(prs[0], 'title')
            self.assertEqual(title, 'bpo-1 bpo-2 bpo-3')

    def testPullRequestEventWithoutIssueReference(self):
        # When no issue is referenced in PR and environment variable is set
        dummy_client = self._make_client("pullrequestevent2.txt")
        self.assertEqual(self.db.issue.count(), 1)
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        self.assertEqual(self.db.issue.count(), 2)
        user_id = self.db.issue.get('2', 'creator')
        self.assertEqual(self.db.user.get(user_id, 'username'), 'anonymous')

    def testPullRequestEventWithoutBody(self):
        # When the body of the PR is null and environment variable is set
        dummy_client = self._make_client("pullrequestevent6.txt")
        self.db.issue.create(title="Issue 2")
        self.db.issue.create(title="Issue 3")
        self.assertEqual(self.db.issue.count(), 3)
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        self.assertEqual(self.db.issue.count(), 3)
        for i in range(1, 4):
            prs = self.db.issue.get(str(i), 'pull_requests')
            self.assertEqual(len(prs), 1)
            number = self.db.pull_request.get(prs[0], 'number')
            self.assertEqual(number, '11')
            title = self.db.pull_request.get(prs[0], 'title')
            self.assertEqual(title, 'bpo-1 bpo-2 bpo-3')

    def testPullRequestWithOneNonExistentIssue(self):
        # When one of the issues does not exists, the existing ones should
        # still be linked, and that non-existent should be ignored
        dummy_client = self._make_client("pullrequestevent7.txt")
        self.db.issue.create(title="Issue 2")
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        for i in range(1, 3):
            prs = self.db.issue.get(str(i), 'pull_requests')
            self.assertEqual(len(prs), 1)
            number = self.db.pull_request.get(prs[0], 'number')
            self.assertEqual(number, '11')
            title = self.db.pull_request.get(prs[0], 'title')
            self.assertEqual(title, 'bpo-1 bpo-2 bpo-3')

    def testEditPullRequestWithOneNonExistentIssue(self):
        # When one of the issues does not exists, the existing ones should
        # still be updated, and that non-existent should be ignored
        dummy_client = self._make_client("pullrequestevent8.txt")
        pr = self.db.pull_request.create(number='1', title='Some title')
        self.db.issue.set('1', pull_requests=[pr])
        self.db.issue.create(title="Issue 2")
        pr = self.db.pull_request.create(number='1', title='Some title')
        self.db.issue.set('2', pull_requests=[pr])
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        for i in range(1, 3):
            prs = self.db.issue.get(str(i), 'pull_requests')
            self.assertEqual(len(prs), 1)
            number = self.db.pull_request.get(prs[0], 'number')
            self.assertEqual(number, '1')
            title = self.db.pull_request.get(prs[0], 'title')
            self.assertEqual(title, 'Title after edit: bpo-1, bpo-2, bpo-3')

    def testPullRequestFromGitHubUserWithoutIssueReference(self):
        # When no issue is referenced in PR and environment variable is set
        # and Github field of b.p.o user is set
        dummy_client = self._make_client("pullrequestevent2.txt")
        self.db.user.create(username="anish.shah", github="AnishShah")
        self.assertEqual(self.db.issue.count(), 1)
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        self.assertEqual(self.db.issue.count(), 2)
        user_id = self.db.issue.get('2', 'creator')
        self.assertEqual(self.db.user.get(user_id, 'username'), 'anish.shah')

    def testPullRequestEventWithoutIssueReferenceAndEnvVariable(self):
        # When no issue is referenced in PR and no environment variable is set
        os.environ.pop('CREATE_ISSUE')
        dummy_client = self._make_client("pullrequestevent2.txt")
        self.assertEqual(self.db.issue.count(), 1)
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        self.assertEqual(self.db.issue.count(), 1)

    def testMergedPullRequest(self):
        # When pull request is merged
        dummy_client = self._make_client('pullrequestevent.txt')
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        prs = self.db.issue.get('1', 'pull_requests')
        self.assertEqual(len(prs), 1)
        number = self.db.pull_request.get(prs[0], 'number')
        self.assertEqual(number, '11')
        status = self.db.pull_request.get(prs[0], 'status')
        self.assertEqual(status, 'open')
        self.db.close()
        dummy_client = self._make_client('pullrequestmerged.txt')
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        status = self.db.pull_request.get(prs[0], 'status')
        self.assertEqual(status, 'merged')

    def testClosedPullRequest(self):
        # When pull request is closed
        dummy_client = self._make_client('pullrequestevent.txt')
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        prs = self.db.issue.get('1', 'pull_requests')
        self.assertEqual(len(prs), 1)
        number = self.db.pull_request.get(prs[0], 'number')
        self.assertEqual(number, '11')
        status = self.db.pull_request.get(prs[0], 'status')
        self.assertEqual(status, 'open')
        self.db.close()
        dummy_client = self._make_client('pullrequestclosed.txt')
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        status = self.db.pull_request.get(prs[0], 'status')
        self.assertEqual(status, 'closed')

    def testReopenedPullRequest(self):
        # When pull request is closed
        dummy_client = self._make_client('pullrequestevent.txt')
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        prs = self.db.issue.get('1', 'pull_requests')
        self.assertEqual(len(prs), 1)
        number = self.db.pull_request.get(prs[0], 'number')
        self.assertEqual(number, '11')
        status = self.db.pull_request.get(prs[0], 'status')
        self.assertEqual(status, 'open')
        self.db.close()
        dummy_client = self._make_client('pullrequestclosed.txt')
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        status = self.db.pull_request.get(prs[0], 'status')
        self.assertEqual(status, 'closed')
        self.db.close()
        dummy_client = self._make_client('pullrequestreopened.txt')
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        status = self.db.pull_request.get(prs[0], 'status')
        self.assertEqual(status, 'open')

    def testClosedPullRequestNonASCII(self):
        # When pull request is closed and the title is non-ASCII
        dummy_client = self._make_client('pullrequestclosed2.txt')
        pr = self.db.pull_request.create(number='11', title='Some title')
        self.db.issue.set('1', pull_requests=[pr])
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        status = self.db.pull_request.get(pr, 'status')
        self.assertEqual(status, 'closed')
        title = self.db.pull_request.get(pr, 'title')
        self.assertEqual(title,
                         '\xf0\x9f\x90\x8d\xf0\x9f\x90\x8d\xf0\x9f\x90\x8d')

    def testPushEventAddsComment(self):
        dummy_client = self._make_client('pushevent.txt')
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        msgs = self.db.issue.get('1', 'messages')
        self.assertEqual(len(msgs), 1)
        content = self.db.msg.get(msgs[0], 'content')
        self.assertIn("""New changeset 65c3a074262662a2c55109ff9a2456ee7647fcc9 by Maciej Szulik in branch 'master':
bpo-1: fix tests.
https://github.com/python/cpython/commit/65c3a074262662a2c55109ff9a2456ee7647fcc9
""",
            content)
        self.assertIsInstance(self.db.msg.get(msgs[0], 'creation'), Date)
        self.assertIsInstance(self.db.msg.get(msgs[0], 'date'), Date)
        # issue status
        status = self.db.issue.get('1', 'status')
        self.assertNotEqual(self.db.status.get(status, 'name'), 'closed')
        self.assertIsNone(self.db.issue.get('1', 'resolution'))
        self.assertIsNone(self.db.issue.get('1', 'stage'))

    def testPushEventAddsCommentAndClose(self):
        dummy_client = self._make_client('pushevent1.txt')
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        msgs = self.db.issue.get('1', 'messages')
        self.assertEqual(len(msgs), 1)
        content = self.db.msg.get(msgs[0], 'content')
        self.assertIn("""New changeset 65c3a074262662a2c55109ff9a2456ee7647fcc9 by Maciej Szulik in branch 'master':
closes bpo-1: fix tests.
https://github.com/python/cpython/commit/65c3a074262662a2c55109ff9a2456ee7647fcc9
""",
            content)
        # issue status
        status = self.db.issue.get('1', 'status')
        self.assertEqual(self.db.status.get(status, 'name'), 'closed')
        resolution = self.db.issue.get('1', 'resolution')
        self.assertEqual(self.db.resolution.get(resolution, 'name'), 'fixed')
        stage = self.db.issue.get('1', 'stage')
        self.assertEqual(self.db.stage.get(stage, 'name'), 'resolved')

    def testPushEventWithMultipleCommitsSingleIssue(self):
        dummy_client = self._make_client('pushevent2.txt')
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        msgs = self.db.issue.get('1', 'messages')
        self.assertEqual(len(msgs), 1)
        content = self.db.msg.get(msgs[0], 'content')
        self.assertIn("""New changeset 65c3a074262662a2c55109ff9a2456ee7647fcc9 by Maciej Szulik in branch '2.7':
bpo-1: fix tests.
https://github.com/python/cpython/commit/65c3a074262662a2c55109ff9a2456ee7647fcc9

New changeset 4488ebcdf2d16393d1a78c4105e4a18e4d0d77af by Maciej Szulik in branch '2.7':
bpo-1: fix else.
https://github.com/python/cpython/commit/4488ebcdf2d16393d1a78c4105e4a18e4d0d77af
""",
            content)
                # issue status
        status = self.db.issue.get('1', 'status')
        self.assertNotEqual(self.db.status.get(status, 'name'), 'closed')
        self.assertIsNone(self.db.issue.get('1', 'resolution'))
        self.assertIsNone(self.db.issue.get('1', 'stage'))

    def testPushEventWithMultipleCommitsSingleIssueAndClose(self):
        dummy_client = self._make_client('pushevent3.txt')
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        msgs = self.db.issue.get('1', 'messages')
        self.assertEqual(len(msgs), 1)
        content = self.db.msg.get(msgs[0], 'content')
        self.assertIn("""New changeset 65c3a074262662a2c55109ff9a2456ee7647fcc9 by Maciej Szulik (Anish Shah) in branch '3.5':
closing bpo-1: fix tests.
https://github.com/python/cpython/commit/65c3a074262662a2c55109ff9a2456ee7647fcc9

New changeset 4488ebcdf2d16393d1a78c4105e4a18e4d0d77af by Maciej Szulik in branch '3.5':
bpo-1: fix else.
https://github.com/python/cpython/commit/4488ebcdf2d16393d1a78c4105e4a18e4d0d77af
""",
            content)
        # issue status
        status = self.db.issue.get('1', 'status')
        self.assertEqual(self.db.status.get(status, 'name'), 'closed')
        resolution = self.db.issue.get('1', 'resolution')
        self.assertEqual(self.db.resolution.get(resolution, 'name'), 'fixed')
        stage = self.db.issue.get('1', 'stage')
        self.assertEqual(self.db.stage.get(stage, 'name'), 'resolved')

    def testPushEventWithMultipleCommitsMultipleIssues(self):
        dummy_client = self._make_client('pushevent4.txt')
        self.db.issue.create(title="Issue 2")
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        # first issue messages
        msgs = self.db.issue.get('1', 'messages')
        self.assertEqual(len(msgs), 1)
        content = self.db.msg.get(msgs[0], 'content')
        self.assertIn("""New changeset 65c3a074262662a2c55109ff9a2456ee7647fcc9 by Maciej Szulik in branch '3.6':
closes bpo-1: fix tests.
https://github.com/python/cpython/commit/65c3a074262662a2c55109ff9a2456ee7647fcc9
""",
            content)
        # first issue status
        status = self.db.issue.get('1', 'status')
        self.assertEqual(self.db.status.get(status, 'name'), 'closed')
        resolution = self.db.issue.get('1', 'resolution')
        self.assertEqual(self.db.resolution.get(resolution, 'name'), 'fixed')
        stage = self.db.issue.get('1', 'stage')
        self.assertEqual(self.db.stage.get(stage, 'name'), 'resolved')
        # second issue messages
        msgs = self.db.issue.get('2', 'messages')
        self.assertEqual(len(msgs), 1)
        content = self.db.msg.get(msgs[0], 'content')
        self.assertIn("""New changeset 4488ebcdf2d16393d1a78c4105e4a18e4d0d77af by Maciej Szulik in branch '3.6':
bpo-2: fix else.
https://github.com/python/cpython/commit/4488ebcdf2d16393d1a78c4105e4a18e4d0d77af
""",
            content)
        # second issue status
        status = self.db.issue.get('2', 'status')
        self.assertNotEqual(self.db.status.get(status, 'name'), 'closed')
        self.assertIsNone(self.db.issue.get('2', 'resolution'))
        self.assertIsNone(self.db.issue.get('2', 'stage'))

    def testPushEventNotForMainBranches(self):
        # message should be added only if commit is pushed into master/2.x/3.x branches
        dummy_client = self._make_client('pushevent5.txt')
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        # issue should not have any messages
        msgs = self.db.issue.get('1', 'messages')
        self.assertEqual(len(msgs), 0)

    def testPushEvent613(self):
        dummy_client = self._make_client('pushevent6.txt')
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        msgs = self.db.issue.get('1', 'messages')
        self.assertEqual(len(msgs), 1)
        content = self.db.msg.get(msgs[0], 'content')
        self.assertIn("""New changeset 9d07aceedabcdc9826489f8b9baffff056283bb3 by Brett Cannon in branch '3.6':
bpo-1: Mention coverage.py in trace module documentation (GH-435)
https://github.com/python/cpython/commit/9d07aceedabcdc9826489f8b9baffff056283bb3
""",
            content)

def test_suite():
    suite = unittest.TestSuite()
    for l in list_backends():
        dct = dict(backend=l)
        subcls = type(TestCase)('TestCase_%s' % l, (TestCase,), dct)
        suite.addTest(unittest.makeSuite(subcls))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    unittest.main(testRunner=runner)
