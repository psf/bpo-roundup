# $Id: test_config.py,v 1.1.2.1 2002-02-06 07:11:13 richard Exp $

import unittest, time, tempfile, shutil, os

from roundup import config

class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.filename = tempfile.mktemp()
        os.makedirs(self.filename)
        open(os.path.join(self.filename, 'roundup.rc'), 'w').write('''
[BASE]
http_port = 80
database = %%(instance_home)s/db
templates = %%(instance_home)s/html
log = %%(instance_home)s/log
filter_position = bottom
anonymous_access = deny
anonymous_register = deny
messages_to_author = no
email_signature_position = bottom

[%s]

'''%self.filename)
        open(os.path.join(self.filename, 'config.rc'), 'w').write('''
[DEFAULT]
instance_name=My Test Instance
mailhost=mail.host
mail_domain=blah.dot.com
issue_tracker_email=rjones@%(mail_domain)s
issue_tracker_web=http://localhost:8080/
admin_email=rjones@ekit-inc.com

[MAIL GATEWAY]

[HTTP SERVER]
http_port = 8080

[CGI]

[ADMIN]
''')

    def tearDown(self):
        shutil.rmtree(self.filename)

    def testVars(self):
        os.environ['ROUNDUP_CONF'] = os.path.join(self.filename, 'roundup.rc')
        cfg = config.loadBaseConfig()
        home, = cfg.listInstances()
        inst = cfg.loadInstanceConfig(home)
        self.assertEquals(inst.sections(), ['MAIL GATEWAY',
            'ADMIN', 'HTTP SERVER', 'CGI'])
        for section in inst.sections():
            self.assertEquals(inst.options(section), ['admin_email',
                'email_signature_position', 'anonymous_register',
                'instance_home', 'filter_position', 'issue_tracker_web',
                'instance_name', 'database', 'mailhost', 'templates',
                'mail_domain', 'issue_tracker_email', 'log',
                'messages_to_author', 'http_port', 'anonymous_access'])
        self.assertEquals(inst.getint('HTTP SERVER', 'http_port'), 8080)
        self.assertEquals(inst.getint('CGI', 'http_port'), 80)

def suite():
   return unittest.makeSuite(ConfigTest, 'test')


#
# $Log: not supported by cvs2svn $
#
# vim: set filetype=python ts=4 sw=4 et si
