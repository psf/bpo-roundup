import sys
import os
import ConfigParser
import string

class Error(Exception):
    pass

def debug_mode():
    """
    Returns the basic debug mode/level.
    """
    return os.environ.get('ROUNDUP_DEBUG', 0)

def load_base_config():
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

    def load_instances_config(self):
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

    def get_instance_names(self):
        return self.instance_dirs.keys()

    def get_instance_name(self, dir):
        return self.instance_names[dir]

    def get_instance_dir(self, name):
        return self.instance_dirs[name]

    def load_instance_config(self, name):
        instance_dir = self.get_instance_dir(name)
        
        defaults_file = self.conf.get(name, 'defaults')
        config_file = self.conf.get(name, 'config')

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
    base_config = load_base_config()
    instances_config = base_config.load_instances_config()
    
    for k in instances_config.get_instance_names():
        print "%s:%s"%(k, instances_config.get_instance_dir(k),)
