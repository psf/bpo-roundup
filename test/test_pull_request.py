import unittest
import os
import db_test_base
import cgi
from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO
from roundup.cgi import client
from roundup.backends import list_backends
from roundup.pull_request import GitHubHandler
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
        # When the title of a PR has string "bpo123"
        dummy_client = self._make_client("pullrequestevent.txt")
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        prs = self.db.issue.get('1', 'pull_requests')
        self.assertEqual(len(prs), 1)
        number = self.db.pull_request.get(prs[0], 'number')
        self.assertEqual(number, '11')
        user_id = self.db.pull_request.get(prs[0], 'creator')
        self.assertEqual(self.db.user.get(user_id, 'username'), 'anonymous')

    def testPullRequestEventForTitle2(self):
        # When the title of a PR has string with space "bpo 123"
        dummy_client = self._make_client("pullrequestevent5.txt")
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        prs = self.db.issue.get('1', 'pull_requests')
        self.assertEqual(len(prs), 1)
        number = self.db.pull_request.get(prs[0], 'number')
        self.assertEqual(number, '11')
        user_id = self.db.pull_request.get(prs[0], 'creator')
        self.assertEqual(self.db.user.get(user_id, 'username'), 'anonymous')

    def testPullRequestEventForBody(self):
        # When the body of a PR has string "bpo123"
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
            self.assertEqual(title, 'fixes bpo1, bpo2, bpo3')

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
        # When both title and body of a PR has multiple and duplicated "bpo123"
        dummy_client = self._make_client("pullrequestevent6.txt")
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
            self.assertEqual(title, 'bpo1 bpo2 bpo 3')

    def testPullRequestEventWithoutIssueReference(self):
        # When no issue is referenced in PR and environment variable is set
        dummy_client = self._make_client("pullrequestevent2.txt")
        self.assertEqual(self.db.issue.count(), 1)
        handler = GitHubHandler(dummy_client)
        handler.dispatch()
        self.assertEqual(self.db.issue.count(), 2)
        user_id = self.db.issue.get('2', 'creator')
        self.assertEqual(self.db.user.get(user_id, 'username'), 'anonymous')

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
