import sys
import os
import ConfigParser
import string

class Error(Exception):
    pass

class UnknownInstanceLocation(Error):
    pass

class NoInstanceConfigFile(Error):
    pass

def debug_mode():
    """
    Returns the basic debug mode/level.
    """
    return os.environ.get('ROUNDUP_DEBUG', 0)

def loadBaseConfig():
    """
    Loads the base configuration for Roundup.
    """
    
    c = ConfigParser.ConfigParser()

    ##
    ## CTB: this is where to search for all overrides, including
    ##      system-specific files, registry settings, etc.
    ##

    # For the moment, search for the config file in
    #
    #      %(sys.prefix)s/share/roundup/roundup.rc,
    #
    # with ROUNDUP_CONF overriding it.
    
    filenames_to_check = []             # list of files to check:
    if os.environ.has_key('ROUNDUP_CONF'):
        filenames_to_check.append(os.environ['ROUNDUP_CONF'])
        
    filenames_to_check.append('%s/share/roundup/roundup.rc'%(sys.prefix,))

    for filename in filenames_to_check:
        if os.path.exists(filename):
            c.read(filename)
            break
    else:
        raise Error("could not find configuration file")

    if debug_mode():
        print 'Loaded configuration from "%s".'%(filename,)

    # we also want to give a base path for other config file names;
    # for the moment, make it the base path of the filename we chose.
    base_path = os.path.dirname(filename)

    return BaseConfig(c, base_path)

class BaseConfig:
    """
    A container for the installation-wide roundup configuration.
    """
    def __init__(self, c, base_path):
        assert isinstance(c, ConfigParser.ConfigParser)
        self.conf = c
        self.base_path = base_path

    def get(self, group, attr):
        return self.conf.get(group, attr)

    def loadInstances(self):
        filename = string.strip(self.conf.get('base', 'instances'))

        # if it looks like an absolute path, leave it alone; otherwise,
        # add on the base path.
        if filename[0] == '/' or filename[0] == '\\':
            pass
        else:
            filename = os.path.normpath(self.base_path + '/' + filename)

        defaults_dictionary = { 'roundup_conf_dir' : self.base_path }

        c = ConfigParser.ConfigParser(defaults_dictionary)
        c.read(filename)

        return InstancesConfig(c, filename)

class InstancesConfig:
    """
    A container for the installation-wide list of instances.
    """
    def __init__(self, c, filename=""):
        assert isinstance(c, ConfigParser.ConfigParser)
        self.conf = c
        self.filename = filename

        instance_names = {}
        instance_dirs = {}
        
        for name in c.sections():
            dir = c.get(name, 'homedir')

            if instance_names.has_key(dir) or instance_dirs.has_key(name):
                error_text = 'ERROR: dir/name correspondence is not unique (%s)'%(self.filename,)
                raise ValueError(error_text)
            
            instance_dirs[name] = dir
            instance_names[dir] = name

        self.instance_dirs = instance_dirs
        self.instance_names = instance_names

    def getNames(self):
        return self.instance_dirs.keys()

    def getNameFromDir(self, dir):
        if self.instance_names.has_key(dir):
            return self.instance_names[dir]
        else:
            raise UnknownInstanceLocation(dir)

    def getDirFromName(self, name):
        return self.instance_dirs[name]

    def loadConfig(self, name):
        instance_dir = self.getDirFromName(name)
        
        defaults_file = self.conf.get(name, 'defaults')
        if not os.path.exists(defaults_file):
            raise NoInstanceConfigFile("defaults file %s does not exist"%(defaults_file,))
        
        config_file = self.conf.get(name, 'config')
        if not os.path.exists(config_file):
            raise NoInstanceConfigFile("%s does not exist"%(config_file,))

        defaults_dictionary = { 'homedir' : instance_dir,
                                'instance_name' : name,
                              }


        c = ConfigParser.ConfigParser(defaults_dictionary)
        c.read(defaults_file)
        c.read(config_file)

        return InstanceConfig(c, name, instance_dir)

class InstanceConfig:
    """
    A container for each per-instance configuration.
    """
    
    def __init__(self, c, instanceName, instanceDirectory):
        assert isinstance(c, ConfigParser.ConfigParser)
        self.conf = c
        self.name = instanceName
        self.directory = instanceDirectory

    def get_name(self):
        return self.name

    def get_directory(self):
        return self.directory

    def get(self, group, attr):
        return self.conf.get(group, attr)
            
if __name__ == '__main__':
    base_config = loadBaseConfig()
    instances = base_config.loadInstances()
    
    for k in instances.getNames():
        print "%s:%s"%(k, instances.getDirFromName(k),)
