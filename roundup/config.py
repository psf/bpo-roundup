'''Organise the configuration files for roundup installations.

There's two configuration files of interest to any given roundup instance:

roundup.rc:
  This is the global configuration file. It specifies:
    . default configuration variable values
    . instance names and locations

<instance home>/config.rc:
  This defines the configuration overrides for the instance

Config values are determined in order:
 1. instance config application-specific section:
     'MAIL GATEWAY'
     'HTTP SERVER'
     'CGI'
     'ADMIN'
 2. instance config 'DEFAULT' with some added vars:
     'instance_home': the home dir
 3. all the entries from the roundup.rc global '[DEFAULT]'
 4. pre-set application defaults (in this file)

Some variables will raise errors if an attempt is made to look them up
using the application defaults:
  . mailhost
  . mail_domain
  . issue_tracker_email
  . issue_tracker_web
  . admin_email

'''
import sys, os, ConfigParser

class Error(Exception):
    pass

class UnknownInstanceLocation(Error):
    pass

class NoInstanceConfigFile(Error):
    pass

def debug_mode():
    """Returns the basic debug mode/level.
    """
    return os.environ.get('ROUNDUP_DEBUG', 0)

def loadBaseConfig():
    """Loads the base configuration for Roundup.
    """
    

    # CTB: this is where to search for all overrides, including
    #      system-specific files, registry settings, etc.
    #
    # For the moment, search for the config file in
    #
    #      ${ROUNDUP_CONF}/roundup.rc
    #      %(sys.prefix)s/share/roundup/roundup.rc,
    # 
    filenames_to_check = []             # list of files to check:
    if os.environ.has_key('ROUNDUP_CONF'):
        filenames_to_check.append(os.environ['ROUNDUP_CONF'])
    filenames_to_check.append('%s/share/roundup/roundup.rc'%sys.prefix)

    # right, now try to get a config
    for filename in filenames_to_check:
        if os.path.exists(filename):
            break
    else:
        raise Error("could not find configuration file")

    if debug_mode():
        print 'Loaded configuration from "%s".'%(filename,)

    return BaseConfig(filename)

class BaseConfig:
    """A container for the installation-wide roundup configuration.
    """
    def __init__(self, filename):
        self.filename = filename
        self.conf = ConfigParser.ConfigParser()
        self.conf.read(filename)

    def get(self, group, attr):
        return self.conf.get(group, attr)

    def listInstances(self):
        return filter(lambda x:x!='BASE', self.conf.sections())

    def loadInstanceConfig(self, home):
        # set up the defaults for the instance config
        defaults = {
            'instance_home': home,
            'http_port': '80',
            'database': '%(instance_home)s/db',
            'templates': '%(instance_home)s/html',
            'log': '%(instance_home)s/log',
            'filter_position': 'bottom',
            'anonymous_access': 'deny',
            'anonymous_register': 'deny',
            'messages_to_author': 'no',
            'email_signature_position': 'bottom',
        }
        for option in self.conf.options('BASE'):
            defaults[option] = self.conf.get('BASE', option, 1)
        
        # make the instance config
        inst = InstanceConfig(defaults)
        inst.read(os.path.join(home, 'config.rc'))
        inst.validate()
        return inst


class InstanceConfig(ConfigParser.ConfigParser):
    """A container for each per-instance configuration.
    """
    def validate(self):
        '''Make sure the config is complete
        '''
        assert self.has_option('BASE', 'instance_name')
        assert self.has_option('BASE', 'mailhost')
        assert self.has_option('BASE', 'mail_domain')
        assert self.has_option('BASE', 'issue_tracker_email')
        assert self.has_option('BASE', 'issue_tracker_web')
        assert self.has_option('BASE', 'admin_email')

    def getBase(self, name):
        '''Convenience wrapper
        '''
        return self.get('BASE', name)

    def getMailGW(self, name):
        '''Look up a var for the mail gateway
        '''
        return self.get('MAIL GATEWAY', name)

    def getHTTPServer(self, name):
        '''Look up a var for the standalone HTTP server
        '''
        return self.get('HTTP SERVER', name)

    def getCGI(self, name):
        '''Look up a var for the cgi script
        '''
        return self.get('CGI', name)

    def getAdmin(self, name):
        '''Look up a var for the admin script
        '''
        return self.get('ADMIN', name)

    def get_default_database_dir(self):
        '''Historical method to allow migration to using this new config
        system...
        '''
        return self.get('BASE', 'DATABASE')

