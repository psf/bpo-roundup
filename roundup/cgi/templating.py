import sys, cgi, urllib, os, re, os.path, time, errno

from roundup import hyperdb, date
from roundup.i18n import _

try:
    import cPickle as pickle
except ImportError:
    import pickle
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
try:
    import StructuredText
except ImportError:
    StructuredText = None

# bring in the templating support
from roundup.cgi.PageTemplates import PageTemplate
from roundup.cgi.PageTemplates.Expressions import getEngine
from roundup.cgi.TAL.TALInterpreter import TALInterpreter
from roundup.cgi import ZTUtils

class NoTemplate(Exception):
    pass

class Templates:
    templates = {}

    def __init__(self, dir):
        self.dir = dir

    def precompileTemplates(self):
        ''' Go through a directory and precompile all the templates therein
        '''
        for filename in os.listdir(self.dir):
            if os.path.isdir(filename): continue
            if '.' in filename:
                name, extension = filename.split('.')
                self.getTemplate(name, extension)
            else:
                self.getTemplate(filename, None)

    def get(self, name, extension):
        ''' Interface to get a template, possibly loading a compiled template.

            "name" and "extension" indicate the template we're after, which in
            most cases will be "name.extension". If "extension" is None, then
            we look for a template just called "name" with no extension.

            If the file "name.extension" doesn't exist, we look for
            "_generic.extension" as a fallback.
        '''
        # default the name to "home"
        if name is None:
            name = 'home'

        # find the source, figure the time it was last modified
        if extension:
            filename = '%s.%s'%(name, extension)
        else:
            filename = name
        src = os.path.join(self.dir, filename)
        try:
            stime = os.stat(src)[os.path.stat.ST_MTIME]
        except os.error, error:
            if error.errno != errno.ENOENT:
                raise
            if not extension:
                raise NoTemplate, 'Template file "%s" doesn\'t exist'%name

            # try for a generic template
            generic = '_generic.%s'%extension
            src = os.path.join(self.dir, generic)
            try:
                stime = os.stat(src)[os.path.stat.ST_MTIME]
            except os.error, error:
                if error.errno != errno.ENOENT:
                    raise
                # nicer error
                raise NoTemplate, 'No template file exists for templating '\
                    '"%s" with template "%s" (neither "%s" nor "%s")'%(name,
                    extension, filename, generic)
            filename = generic

        if self.templates.has_key(src) and \
                stime < self.templates[src].mtime:
            # compiled template is up to date
            return self.templates[src]

        # compile the template
        self.templates[src] = pt = RoundupPageTemplate()
        pt.write(open(src).read())
        pt.id = filename
        pt.mtime = time.time()
        return pt

    def __getitem__(self, name):
        name, extension = os.path.splitext(name)
        if extension:
            extension = extension[1:]
        try:
            return self.get(name, extension)
        except NoTemplate, message:
            raise KeyError, message

class RoundupPageTemplate(PageTemplate.PageTemplate):
    ''' A Roundup-specific PageTemplate.

        Interrogate the client to set up the various template variables to
        be available:

        *context*
         this is one of three things:
         1. None - we're viewing a "home" page
         2. The current class of item being displayed. This is an HTMLClass
            instance.
         3. The current item from the database, if we're viewing a specific
            item, as an HTMLItem instance.
        *request*
          Includes information about the current request, including:
           - the url
           - the current index information (``filterspec``, ``filter`` args,
             ``properties``, etc) parsed out of the form. 
           - methods for easy filterspec link generation
           - *user*, the current user node as an HTMLItem instance
           - *form*, the current CGI form information as a FieldStorage
        *config*
          The current tracker config.
        *db*
          The current database, used to access arbitrary database items.
        *utils*
          This is a special class that has its base in the TemplatingUtils
          class in this file. If the tracker interfaces module defines a
          TemplatingUtils class then it is mixed in, overriding the methods
          in the base class.
    '''
    def getContext(self, client, classname, request):
        # construct the TemplatingUtils class
        utils = TemplatingUtils
        if hasattr(client.instance.interfaces, 'TemplatingUtils'):
            class utils(client.instance.interfaces.TemplatingUtils, utils):
                pass

        c = {
             'options': {},
             'nothing': None,
             'request': request,
             'db': HTMLDatabase(client),
             'config': client.instance.config,
             'tracker': client.instance,
             'utils': utils(client),
             'templates': Templates(client.instance.config.TEMPLATES),
        }
        # add in the item if there is one
        if client.nodeid:
            if classname == 'user':
                c['context'] = HTMLUser(client, classname, client.nodeid)
            else:
                c['context'] = HTMLItem(client, classname, client.nodeid)
        elif client.db.classes.has_key(classname):
            c['context'] = HTMLClass(client, classname)
        return c

    def render(self, client, classname, request, **options):
        """Render this Page Template"""

        if not self._v_cooked:
            self._cook()

        __traceback_supplement__ = (PageTemplate.PageTemplateTracebackSupplement, self)

        if self._v_errors:
            raise PageTemplate.PTRuntimeError, \
                'Page Template %s has errors.'%self.id

        # figure the context
        classname = classname or client.classname
        request = request or HTMLRequest(client)
        c = self.getContext(client, classname, request)
        c.update({'options': options})

        # and go
        output = StringIO.StringIO()
        TALInterpreter(self._v_program, self.macros,
            getEngine().getContext(c), output, tal=1, strictinsert=0)()
        return output.getvalue()

class HTMLDatabase:
    ''' Return HTMLClasses for valid class fetches
    '''
    def __init__(self, client):
        self._client = client

        # we want config to be exposed
        self.config = client.db.config

    def __getitem__(self, item):
        self._client.db.getclass(item)
        return HTMLClass(self._client, item)

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError, attr

    def classes(self):
        l = self._client.db.classes.keys()
        l.sort()
        return [HTMLClass(self._client, cn) for cn in l]

def lookupIds(db, prop, ids, num_re=re.compile('-?\d+')):
    cl = db.getclass(prop.classname)
    l = []
    for entry in ids:
        if num_re.match(entry):
            l.append(entry)
        else:
            try:
                l.append(cl.lookup(entry))
            except KeyError:
                # ignore invalid keys
                pass
    return l

class HTMLPermissions:
    ''' Helpers that provide answers to commonly asked Permission questions.
    '''
    def is_edit_ok(self):
        ''' Is the user allowed to Edit the current class?
        '''
        return self._db.security.hasPermission('Edit', self._client.userid,
            self._classname)
    def is_view_ok(self):
        ''' Is the user allowed to View the current class?
        '''
        return self._db.security.hasPermission('View', self._client.userid,
            self._classname)
    def is_only_view_ok(self):
        ''' Is the user only allowed to View (ie. not Edit) the current class?
        '''
        return self.is_view_ok() and not self.is_edit_ok()

class HTMLClass(HTMLPermissions):
    ''' Accesses through a class (either through *class* or *db.<classname>*)
    '''
    def __init__(self, client, classname):
        self._client = client
        self._db = client.db

        # we want classname to be exposed, but _classname gives a
        # consistent API for extending Class/Item
        self._classname = self.classname = classname
        self._klass = self._db.getclass(self.classname)
        self._props = self._klass.getprops()

    def __repr__(self):
        return '<HTMLClass(0x%x) %s>'%(id(self), self.classname)

    def __getitem__(self, item):
        ''' return an HTMLProperty instance
        '''
       #print 'HTMLClass.getitem', (self, item)

        # we don't exist
        if item == 'id':
            return None

        # get the property
        prop = self._props[item]

        # look up the correct HTMLProperty class
        form = self._client.form
        for klass, htmlklass in propclasses:
            if not isinstance(prop, klass):
                continue
            if form.has_key(item):
                if isinstance(prop, hyperdb.Multilink):
                    value = lookupIds(self._db, prop,
                        handleListCGIValue(form[item]))
                elif isinstance(prop, hyperdb.Link):
                    value = form[item].value.strip()
                    if value:
                        value = lookupIds(self._db, prop, [value])[0]
                    else:
                        value = None
                else:
                    value = form[item].value.strip() or None
            else:
                if isinstance(prop, hyperdb.Multilink):
                    value = []
                else:
                    value = None
            return htmlklass(self._client, '', prop, item, value)

        # no good
        raise KeyError, item

    def __getattr__(self, attr):
        ''' convenience access '''
        try:
            return self[attr]
        except KeyError:
            raise AttributeError, attr

    def getItem(self, itemid, num_re=re.compile('\d+')):
        ''' Get an item of this class by its item id.
        '''
        # make sure we're looking at an itemid
        if not num_re.match(itemid):
            itemid = self._klass.lookup(itemid)

        if self.classname == 'user':
            klass = HTMLUser
        else:
            klass = HTMLItem

        return klass(self._client, self.classname, itemid)

    def properties(self):
        ''' Return HTMLProperty for all of this class' properties.
        '''
        l = []
        for name, prop in self._props.items():
            for klass, htmlklass in propclasses:
                if isinstance(prop, hyperdb.Multilink):
                    value = []
                else:
                    value = None
                if isinstance(prop, klass):
                    l.append(htmlklass(self._client, '', prop, name, value))
        return l

    def list(self):
        ''' List all items in this class.
        '''
        if self.classname == 'user':
            klass = HTMLUser
        else:
            klass = HTMLItem

        # get the list and sort it nicely
        l = self._klass.list()
        sortfunc = make_sort_function(self._db, self.classname)
        l.sort(sortfunc)

        l = [klass(self._client, self.classname, x) for x in l]
        return l

    def csv(self):
        ''' Return the items of this class as a chunk of CSV text.
        '''
        # get the CSV module
        try:
            import csv
        except ImportError:
            return 'Sorry, you need the csv module to use this function.\n'\
                'Get it from: http://www.object-craft.com.au/projects/csv/'

        props = self.propnames()
        p = csv.parser()
        s = StringIO.StringIO()
        s.write(p.join(props) + '\n')
        for nodeid in self._klass.list():
            l = []
            for name in props:
                value = self._klass.get(nodeid, name)
                if value is None:
                    l.append('')
                elif isinstance(value, type([])):
                    l.append(':'.join(map(str, value)))
                else:
                    l.append(str(self._klass.get(nodeid, name)))
            s.write(p.join(l) + '\n')
        return s.getvalue()

    def propnames(self):
        ''' Return the list of the names of the properties of this class.
        '''
        idlessprops = self._klass.getprops(protected=0).keys()
        idlessprops.sort()
        return ['id'] + idlessprops

    def filter(self, request=None):
        ''' Return a list of items from this class, filtered and sorted
            by the current requested filterspec/filter/sort/group args
        '''
        if request is not None:
            filterspec = request.filterspec
            sort = request.sort
            group = request.group
        else:
            filterspec = {}
            sort = (None,None)
            group = (None,None)
        if self.classname == 'user':
            klass = HTMLUser
        else:
            klass = HTMLItem
        l = [klass(self._client, self.classname, x)
             for x in self._klass.filter(None, filterspec, sort, group)]
        return l

    def classhelp(self, properties=None, label='list', width='500',
            height='400'):
        ''' Pop up a javascript window with class help

            This generates a link to a popup window which displays the 
            properties indicated by "properties" of the class named by
            "classname". The "properties" should be a comma-separated list
            (eg. 'id,name,description'). Properties defaults to all the
            properties of a class (excluding id, creator, created and
            activity).

            You may optionally override the label displayed, the width and
            height. The popup window will be resizable and scrollable.
        '''
        if properties is None:
            properties = self._klass.getprops(protected=0).keys()
            properties.sort()
            properties = ','.join(properties)
        return '<a href="javascript:help_window(\'%s?:template=help&' \
            'properties=%s\', \'%s\', \'%s\')"><b>(%s)</b></a>'%(
            self.classname, properties, width, height, label)

    def submit(self, label="Submit New Entry"):
        ''' Generate a submit button (and action hidden element)
        '''
        return '  <input type="hidden" name=":action" value="new">\n'\
        '  <input type="submit" name="submit" value="%s">'%label

    def history(self):
        return 'New node - no history'

    def renderWith(self, name, **kwargs):
        ''' Render this class with the given template.
        '''
        # create a new request and override the specified args
        req = HTMLRequest(self._client)
        req.classname = self.classname
        req.update(kwargs)

        # new template, using the specified classname and request
        pt = Templates(self._db.config.TEMPLATES).get(self.classname, name)

        # use our fabricated request
        return pt.render(self._client, self.classname, req)

class HTMLItem(HTMLPermissions):
    ''' Accesses through an *item*
    '''
    def __init__(self, client, classname, nodeid):
        self._client = client
        self._db = client.db
        self._classname = classname
        self._nodeid = nodeid
        self._klass = self._db.getclass(classname)
        self._props = self._klass.getprops()

    def __repr__(self):
        return '<HTMLItem(0x%x) %s %s>'%(id(self), self._classname,
            self._nodeid)

    def __getitem__(self, item):
        ''' return an HTMLProperty instance
        '''
        #print 'HTMLItem.getitem', (self, item)
        if item == 'id':
            return self._nodeid

        # get the property
        prop = self._props[item]

        # get the value, handling missing values
        value = self._klass.get(self._nodeid, item, None)
        if value is None:
            if isinstance(self._props[item], hyperdb.Multilink):
                value = []

        # look up the correct HTMLProperty class
        for klass, htmlklass in propclasses:
            if isinstance(prop, klass):
                return htmlklass(self._client, self._nodeid, prop, item, value)

        raise KeyErorr, item

    def __getattr__(self, attr):
        ''' convenience access to properties '''
        try:
            return self[attr]
        except KeyError:
            raise AttributeError, attr
    
    def submit(self, label="Submit Changes"):
        ''' Generate a submit button (and action hidden element)
        '''
        return '  <input type="hidden" name=":action" value="edit">\n'\
        '  <input type="submit" name="submit" value="%s">'%label

    def journal(self, direction='descending'):
        ''' Return a list of HTMLJournalEntry instances.
        '''
        # XXX do this
        return []

    def history(self, direction='descending', dre=re.compile('\d+')):
        l = ['<table class="history">'
             '<tr><th colspan="4" class="header">',
             _('History'),
             '</th></tr><tr>',
             _('<th>Date</th>'),
             _('<th>User</th>'),
             _('<th>Action</th>'),
             _('<th>Args</th>'),
            '</tr>']
        comments = {}
        history = self._klass.history(self._nodeid)
        history.sort()
        if direction == 'descending':
            history.reverse()
        for id, evt_date, user, action, args in history:
            date_s = str(evt_date).replace("."," ")
            arg_s = ''
            if action == 'link' and type(args) == type(()):
                if len(args) == 3:
                    linkcl, linkid, key = args
                    arg_s += '<a href="%s%s">%s%s %s</a>'%(linkcl, linkid,
                        linkcl, linkid, key)
                else:
                    arg_s = str(args)

            elif action == 'unlink' and type(args) == type(()):
                if len(args) == 3:
                    linkcl, linkid, key = args
                    arg_s += '<a href="%s%s">%s%s %s</a>'%(linkcl, linkid,
                        linkcl, linkid, key)
                else:
                    arg_s = str(args)

            elif type(args) == type({}):
                cell = []
                for k in args.keys():
                    # try to get the relevant property and treat it
                    # specially
                    try:
                        prop = self._props[k]
                    except KeyError:
                        prop = None
                    if prop is not None:
                        if args[k] and (isinstance(prop, hyperdb.Multilink) or
                                isinstance(prop, hyperdb.Link)):
                            # figure what the link class is
                            classname = prop.classname
                            try:
                                linkcl = self._db.getclass(classname)
                            except KeyError:
                                labelprop = None
                                comments[classname] = _('''The linked class
                                    %(classname)s no longer exists''')%locals()
                            labelprop = linkcl.labelprop(1)
                            hrefable = os.path.exists(
                                os.path.join(self._db.config.TEMPLATES,
                                classname+'.item'))

                        if isinstance(prop, hyperdb.Multilink) and args[k]:
                            ml = []
                            for linkid in args[k]:
                                if isinstance(linkid, type(())):
                                    sublabel = linkid[0] + ' '
                                    linkids = linkid[1]
                                else:
                                    sublabel = ''
                                    linkids = [linkid]
                                subml = []
                                for linkid in linkids:
                                    label = classname + linkid
                                    # if we have a label property, try to use it
                                    # TODO: test for node existence even when
                                    # there's no labelprop!
                                    try:
                                        if labelprop is not None and \
                                                labelprop != 'id':
                                            label = linkcl.get(linkid, labelprop)
                                    except IndexError:
                                        comments['no_link'] = _('''<strike>The
                                            linked node no longer
                                            exists</strike>''')
                                        subml.append('<strike>%s</strike>'%label)
                                    else:
                                        if hrefable:
                                            subml.append('<a href="%s%s">%s</a>'%(
                                                classname, linkid, label))
                                        else:
                                            subml.append(label)
                                ml.append(sublabel + ', '.join(subml))
                            cell.append('%s:\n  %s'%(k, ', '.join(ml)))
                        elif isinstance(prop, hyperdb.Link) and args[k]:
                            label = classname + args[k]
                            # if we have a label property, try to use it
                            # TODO: test for node existence even when
                            # there's no labelprop!
                            if labelprop is not None and labelprop != 'id':
                                try:
                                    label = linkcl.get(args[k], labelprop)
                                except IndexError:
                                    comments['no_link'] = _('''<strike>The
                                        linked node no longer
                                        exists</strike>''')
                                    cell.append(' <strike>%s</strike>,\n'%label)
                                    # "flag" this is done .... euwww
                                    label = None
                            if label is not None:
                                if hrefable:
                                    cell.append('%s: <a href="%s%s">%s</a>\n'%(k,
                                        classname, args[k], label))
                                else:
                                    cell.append('%s: %s' % (k,label))

                        elif isinstance(prop, hyperdb.Date) and args[k]:
                            d = date.Date(args[k])
                            cell.append('%s: %s'%(k, str(d)))

                        elif isinstance(prop, hyperdb.Interval) and args[k]:
                            d = date.Interval(args[k])
                            cell.append('%s: %s'%(k, str(d)))

                        elif isinstance(prop, hyperdb.String) and args[k]:
                            cell.append('%s: %s'%(k, cgi.escape(args[k])))

                        elif not args[k]:
                            cell.append('%s: (no value)\n'%k)

                        else:
                            cell.append('%s: %s\n'%(k, str(args[k])))
                    else:
                        # property no longer exists
                        comments['no_exist'] = _('''<em>The indicated property
                            no longer exists</em>''')
                        cell.append('<em>%s: %s</em>\n'%(k, str(args[k])))
                arg_s = '<br />'.join(cell)
            else:
                # unkown event!!
                comments['unknown'] = _('''<strong><em>This event is not
                    handled by the history display!</em></strong>''')
                arg_s = '<strong><em>' + str(args) + '</em></strong>'
            date_s = date_s.replace(' ', '&nbsp;')
            # if the user's an itemid, figure the username (older journals
            # have the username)
            if dre.match(user):
                user = self._db.user.get(user, 'username')
            l.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'%(
                date_s, user, action, arg_s))
        if comments:
            l.append(_('<tr><td colspan=4><strong>Note:</strong></td></tr>'))
        for entry in comments.values():
            l.append('<tr><td colspan=4>%s</td></tr>'%entry)
        l.append('</table>')
        return '\n'.join(l)

    def renderQueryForm(self):
        ''' Render this item, which is a query, as a search form.
        '''
        # create a new request and override the specified args
        req = HTMLRequest(self._client)
        req.classname = self._klass.get(self._nodeid, 'klass')
        name = self._klass.get(self._nodeid, 'name')
        req.updateFromURL(self._klass.get(self._nodeid, 'url') +
            '&:queryname=%s'%urllib.quote(name))

        # new template, using the specified classname and request
        pt = Templates(self._db.config.TEMPLATES).get(req.classname, 'search')

        # use our fabricated request
        return pt.render(self._client, req.classname, req)

class HTMLUser(HTMLItem):
    ''' Accesses through the *user* (a special case of item)
    '''
    def __init__(self, client, classname, nodeid):
        HTMLItem.__init__(self, client, 'user', nodeid)
        self._default_classname = client.classname

        # used for security checks
        self._security = client.db.security

    _marker = []
    def hasPermission(self, role, classname=_marker):
        ''' Determine if the user has the Role.

            The class being tested defaults to the template's class, but may
            be overidden for this test by suppling an alternate classname.
        '''
        if classname is self._marker:
            classname = self._default_classname
        return self._security.hasPermission(role, self._nodeid, classname)

    def is_edit_ok(self):
        ''' Is the user allowed to Edit the current class?
            Also check whether this is the current user's info.
        '''
        return self._db.security.hasPermission('Edit', self._client.userid,
            self._classname) or self._nodeid == self._client.userid

    def is_view_ok(self):
        ''' Is the user allowed to View the current class?
            Also check whether this is the current user's info.
        '''
        return self._db.security.hasPermission('Edit', self._client.userid,
            self._classname) or self._nodeid == self._client.userid

class HTMLProperty:
    ''' String, Number, Date, Interval HTMLProperty

        Has useful attributes:

         _name  the name of the property
         _value the value of the property if any

        A wrapper object which may be stringified for the plain() behaviour.
    '''
    def __init__(self, client, nodeid, prop, name, value):
        self._client = client
        self._db = client.db
        self._nodeid = nodeid
        self._prop = prop
        self._name = name
        self._value = value
    def __repr__(self):
        return '<HTMLProperty(0x%x) %s %r %r>'%(id(self), self._name, self._prop, self._value)
    def __str__(self):
        return self.plain()
    def __cmp__(self, other):
        if isinstance(other, HTMLProperty):
            return cmp(self._value, other._value)
        return cmp(self._value, other)

class StringHTMLProperty(HTMLProperty):
    hyper_re = re.compile(r'((?P<url>\w{3,6}://\S+)|'
                          r'(?P<email>[-+=%/\w\.]+@[\w\.\-]+)|'
                          r'(?P<item>(?P<class>[a-z_]+)(?P<id>\d+)))')
    def _hyper_repl(self, match):
        if match.group('url'):
            s = match.group('url')
            return '<a href="%s">%s</a>'%(s, s)
        elif match.group('email'):
            s = match.group('email')
            return '<a href="mailto:%s">%s</a>'%(s, s)
        else:
            s = match.group('item')
            s1 = match.group('class')
            s2 = match.group('id')
            try:
                # make sure s1 is a valid tracker classname
                self._db.getclass(s1)
                return '<a href="%s">%s %s</a>'%(s, s1, s2)
            except KeyError:
                return '%s%s'%(s1, s2)

    def plain(self, escape=0, hyperlink=0):
        ''' Render a "plain" representation of the property
            
            "escape" turns on/off HTML quoting
            "hyperlink" turns on/off in-text hyperlinking of URLs, email
                addresses and designators
        '''
        if self._value is None:
            return ''
        if escape:
            s = cgi.escape(str(self._value))
        else:
            s = str(self._value)
        if hyperlink:
            if not escape:
                s = cgi.escape(s)
            s = self.hyper_re.sub(self._hyper_repl, s)
        return s

    def stext(self, escape=0):
        ''' Render the value of the property as StructuredText.

            This requires the StructureText module to be installed separately.
        '''
        s = self.plain(escape=escape)
        if not StructuredText:
            return s
        return StructuredText(s,level=1,header=0)

    def field(self, size = 30):
        ''' Render a form edit field for the property
        '''
        if self._value is None:
            value = ''
        else:
            value = cgi.escape(str(self._value))
            value = '&quot;'.join(value.split('"'))
        return '<input name="%s" value="%s" size="%s">'%(self._name, value, size)

    def multiline(self, escape=0, rows=5, cols=40):
        ''' Render a multiline form edit field for the property
        '''
        if self._value is None:
            value = ''
        else:
            value = cgi.escape(str(self._value))
            value = '&quot;'.join(value.split('"'))
        return '<textarea name="%s" rows="%s" cols="%s">%s</textarea>'%(
            self._name, rows, cols, value)

    def email(self, escape=1):
        ''' Render the value of the property as an obscured email address
        '''
        if self._value is None: value = ''
        else: value = str(self._value)
        if value.find('@') != -1:
            name, domain = value.split('@')
            domain = ' '.join(domain.split('.')[:-1])
            name = name.replace('.', ' ')
            value = '%s at %s ...'%(name, domain)
        else:
            value = value.replace('.', ' ')
        if escape:
            value = cgi.escape(value)
        return value

class PasswordHTMLProperty(HTMLProperty):
    def plain(self):
        ''' Render a "plain" representation of the property
        '''
        if self._value is None:
            return ''
        return _('*encrypted*')

    def field(self, size = 30):
        ''' Render a form edit field for the property.
        '''
        return '<input type="password" name="%s" size="%s">'%(self._name, size)

    def confirm(self, size = 30):
        ''' Render a second form edit field for the property, used for 
            confirmation that the user typed the password correctly. Generates
            a field with name "name:confirm".
        '''
        return '<input type="password" name="%s:confirm" size="%s">'%(
            self._name, size)

class NumberHTMLProperty(HTMLProperty):
    def plain(self):
        ''' Render a "plain" representation of the property
        '''
        return str(self._value)

    def field(self, size = 30):
        ''' Render a form edit field for the property
        '''
        if self._value is None:
            value = ''
        else:
            value = cgi.escape(str(self._value))
            value = '&quot;'.join(value.split('"'))
        return '<input name="%s" value="%s" size="%s">'%(self._name, value, size)

class BooleanHTMLProperty(HTMLProperty):
    def plain(self):
        ''' Render a "plain" representation of the property
        '''
        if self._value is None:
            return ''
        return self._value and "Yes" or "No"

    def field(self):
        ''' Render a form edit field for the property
        '''
        checked = self._value and "checked" or ""
        s = '<input type="radio" name="%s" value="yes" %s>Yes'%(self._name,
            checked)
        if checked:
            checked = ""
        else:
            checked = "checked"
        s += '<input type="radio" name="%s" value="no" %s>No'%(self._name,
            checked)
        return s

class DateHTMLProperty(HTMLProperty):
    def plain(self):
        ''' Render a "plain" representation of the property
        '''
        if self._value is None:
            return ''
        return str(self._value)

    def field(self, size = 30):
        ''' Render a form edit field for the property
        '''
        if self._value is None:
            value = ''
        else:
            value = cgi.escape(str(self._value))
            value = '&quot;'.join(value.split('"'))
        return '<input name="%s" value="%s" size="%s">'%(self._name, value, size)

    def reldate(self, pretty=1):
        ''' Render the interval between the date and now.

            If the "pretty" flag is true, then make the display pretty.
        '''
        if not self._value:
            return ''

        # figure the interval
        interval = date.Date('.') - self._value
        if pretty:
            return interval.pretty()
        return str(interval)

    _marker = []
    def pretty(self, format=_marker):
        ''' Render the date in a pretty format (eg. month names, spaces).

            The format string is a standard python strftime format string.
            Note that if the day is zero, and appears at the start of the
            string, then it'll be stripped from the output. This is handy
            for the situatin when a date only specifies a month and a year.
        '''
        if format is not self._marker:
            return self._value.pretty(format)
        else:
            return self._value.pretty()

    def local(self, offset):
        ''' Return the date/time as a local (timezone offset) date/time.
        '''
        return DateHTMLProperty(self._client, self._nodeid, self._prop,
            self._name, self._value.local(offset))

class IntervalHTMLProperty(HTMLProperty):
    def plain(self):
        ''' Render a "plain" representation of the property
        '''
        if self._value is None:
            return ''
        return str(self._value)

    def pretty(self):
        ''' Render the interval in a pretty format (eg. "yesterday")
        '''
        return self._value.pretty()

    def field(self, size = 30):
        ''' Render a form edit field for the property
        '''
        if self._value is None:
            value = ''
        else:
            value = cgi.escape(str(self._value))
            value = '&quot;'.join(value.split('"'))
        return '<input name="%s" value="%s" size="%s">'%(self._name, value, size)

class LinkHTMLProperty(HTMLProperty):
    ''' Link HTMLProperty
        Include the above as well as being able to access the class
        information. Stringifying the object itself results in the value
        from the item being displayed. Accessing attributes of this object
        result in the appropriate entry from the class being queried for the
        property accessed (so item/assignedto/name would look up the user
        entry identified by the assignedto property on item, and then the
        name property of that user)
    '''
    def __init__(self, *args):
        HTMLProperty.__init__(self, *args)
        # if we're representing a form value, then the -1 from the form really
        # should be a None
        if str(self._value) == '-1':
            self._value = None

    def __getattr__(self, attr):
        ''' return a new HTMLItem '''
       #print 'Link.getattr', (self, attr, self._value)
        if not self._value:
            raise AttributeError, "Can't access missing value"
        if self._prop.classname == 'user':
            klass = HTMLUser
        else:
            klass = HTMLItem
        i = klass(self._client, self._prop.classname, self._value)
        return getattr(i, attr)

    def plain(self, escape=0):
        ''' Render a "plain" representation of the property
        '''
        if self._value is None:
            return ''
        linkcl = self._db.classes[self._prop.classname]
        k = linkcl.labelprop(1)
        value = str(linkcl.get(self._value, k))
        if escape:
            value = cgi.escape(value)
        return value

    def field(self, showid=0, size=None):
        ''' Render a form edit field for the property
        '''
        linkcl = self._db.getclass(self._prop.classname)
        if linkcl.getprops().has_key('order'):  
            sort_on = 'order'  
        else:  
            sort_on = linkcl.labelprop()  
        options = linkcl.filter(None, {}, ('+', sort_on), (None, None))
        # TODO: make this a field display, not a menu one!
        l = ['<select name="%s">'%self._name]
        k = linkcl.labelprop(1)
        if self._value is None:
            s = 'selected '
        else:
            s = ''
        l.append(_('<option %svalue="-1">- no selection -</option>')%s)

        # make sure we list the current value if it's retired
        if self._value and self._value not in options:
            options.insert(0, self._value)

        for optionid in options:
            # get the option value, and if it's None use an empty string
            option = linkcl.get(optionid, k) or ''

            # figure if this option is selected
            s = ''
            if optionid == self._value:
                s = 'selected '

            # figure the label
            if showid:
                lab = '%s%s: %s'%(self._prop.classname, optionid, option)
            else:
                lab = option

            # truncate if it's too long
            if size is not None and len(lab) > size:
                lab = lab[:size-3] + '...'

            # and generate
            lab = cgi.escape(lab)
            l.append('<option %svalue="%s">%s</option>'%(s, optionid, lab))
        l.append('</select>')
        return '\n'.join(l)

    def menu(self, size=None, height=None, showid=0, additional=[],
            **conditions):
        ''' Render a form select list for this property
        '''
        value = self._value

        # sort function
        sortfunc = make_sort_function(self._db, self._prop.classname)

        linkcl = self._db.getclass(self._prop.classname)
        l = ['<select name="%s">'%self._name]
        k = linkcl.labelprop(1)
        s = ''
        if value is None:
            s = 'selected '
        l.append(_('<option %svalue="-1">- no selection -</option>')%s)
        if linkcl.getprops().has_key('order'):  
            sort_on = ('+', 'order')
        else:  
            sort_on = ('+', linkcl.labelprop())
        options = linkcl.filter(None, conditions, sort_on, (None, None))

        # make sure we list the current value if it's retired
        if self._value and self._value not in options:
            options.insert(0, self._value)

        for optionid in options:
            # get the option value, and if it's None use an empty string
            option = linkcl.get(optionid, k) or ''

            # figure if this option is selected
            s = ''
            if value in [optionid, option]:
                s = 'selected '

            # figure the label
            if showid:
                lab = '%s%s: %s'%(self._prop.classname, optionid, option)
            else:
                lab = option

            # truncate if it's too long
            if size is not None and len(lab) > size:
                lab = lab[:size-3] + '...'
            if additional:
                m = []
                for propname in additional:
                    m.append(linkcl.get(optionid, propname))
                lab = lab + ' (%s)'%', '.join(map(str, m))

            # and generate
            lab = cgi.escape(lab)
            l.append('<option %svalue="%s">%s</option>'%(s, optionid, lab))
        l.append('</select>')
        return '\n'.join(l)
#    def checklist(self, ...)

class MultilinkHTMLProperty(HTMLProperty):
    ''' Multilink HTMLProperty

        Also be iterable, returning a wrapper object like the Link case for
        each entry in the multilink.
    '''
    def __len__(self):
        ''' length of the multilink '''
        return len(self._value)

    def __getattr__(self, attr):
        ''' no extended attribute accesses make sense here '''
        raise AttributeError, attr

    def __getitem__(self, num):
        ''' iterate and return a new HTMLItem
        '''
       #print 'Multi.getitem', (self, num)
        value = self._value[num]
        if self._prop.classname == 'user':
            klass = HTMLUser
        else:
            klass = HTMLItem
        return klass(self._client, self._prop.classname, value)

    def __contains__(self, value):
        ''' Support the "in" operator. We have to make sure the passed-in
            value is a string first, not a *HTMLProperty.
        '''
        return str(value) in self._value

    def reverse(self):
        ''' return the list in reverse order
        '''
        l = self._value[:]
        l.reverse()
        if self._prop.classname == 'user':
            klass = HTMLUser
        else:
            klass = HTMLItem
        return [klass(self._client, self._prop.classname, value) for value in l]

    def plain(self, escape=0):
        ''' Render a "plain" representation of the property
        '''
        linkcl = self._db.classes[self._prop.classname]
        k = linkcl.labelprop(1)
        labels = []
        for v in self._value:
            labels.append(linkcl.get(v, k))
        value = ', '.join(labels)
        if escape:
            value = cgi.escape(value)
        return value

    def field(self, size=30, showid=0):
        ''' Render a form edit field for the property
        '''
        sortfunc = make_sort_function(self._db, self._prop.classname)
        linkcl = self._db.getclass(self._prop.classname)
        value = self._value[:]
        if value:
            value.sort(sortfunc)
        # map the id to the label property
        if not linkcl.getkey():
            showid=1
        if not showid:
            k = linkcl.labelprop(1)
            value = [linkcl.get(v, k) for v in value]
        value = cgi.escape(','.join(value))
        return '<input name="%s" size="%s" value="%s">'%(self._name, size, value)

    def menu(self, size=None, height=None, showid=0, additional=[],
            **conditions):
        ''' Render a form select list for this property
        '''
        value = self._value

        # sort function
        sortfunc = make_sort_function(self._db, self._prop.classname)

        linkcl = self._db.getclass(self._prop.classname)
        if linkcl.getprops().has_key('order'):  
            sort_on = ('+', 'order')
        else:  
            sort_on = ('+', linkcl.labelprop())
        options = linkcl.filter(None, conditions, sort_on, (None,None)) 
        height = height or min(len(options), 7)
        l = ['<select multiple name="%s" size="%s">'%(self._name, height)]
        k = linkcl.labelprop(1)

        # make sure we list the current values if they're retired
        for val in value:
            if val not in options:
                options.insert(0, val)

        for optionid in options:
            # get the option value, and if it's None use an empty string
            option = linkcl.get(optionid, k) or ''

            # figure if this option is selected
            s = ''
            if optionid in value or option in value:
                s = 'selected '

            # figure the label
            if showid:
                lab = '%s%s: %s'%(self._prop.classname, optionid, option)
            else:
                lab = option
            # truncate if it's too long
            if size is not None and len(lab) > size:
                lab = lab[:size-3] + '...'
            if additional:
                m = []
                for propname in additional:
                    m.append(linkcl.get(optionid, propname))
                lab = lab + ' (%s)'%', '.join(m)

            # and generate
            lab = cgi.escape(lab)
            l.append('<option %svalue="%s">%s</option>'%(s, optionid,
                lab))
        l.append('</select>')
        return '\n'.join(l)

# set the propclasses for HTMLItem
propclasses = (
    (hyperdb.String, StringHTMLProperty),
    (hyperdb.Number, NumberHTMLProperty),
    (hyperdb.Boolean, BooleanHTMLProperty),
    (hyperdb.Date, DateHTMLProperty),
    (hyperdb.Interval, IntervalHTMLProperty),
    (hyperdb.Password, PasswordHTMLProperty),
    (hyperdb.Link, LinkHTMLProperty),
    (hyperdb.Multilink, MultilinkHTMLProperty),
)

def make_sort_function(db, classname):
    '''Make a sort function for a given class
    '''
    linkcl = db.getclass(classname)
    if linkcl.getprops().has_key('order'):
        sort_on = 'order'
    else:
        sort_on = linkcl.labelprop()
    def sortfunc(a, b, linkcl=linkcl, sort_on=sort_on):
        return cmp(linkcl.get(a, sort_on), linkcl.get(b, sort_on))
    return sortfunc

def handleListCGIValue(value):
    ''' Value is either a single item or a list of items. Each item has a
        .value that we're actually interested in.
    '''
    if isinstance(value, type([])):
        return [value.value for value in value]
    else:
        value = value.value.strip()
        if not value:
            return []
        return value.split(',')

class ShowDict:
    ''' A convenience access to the :columns index parameters
    '''
    def __init__(self, columns):
        self.columns = {}
        for col in columns:
            self.columns[col] = 1
    def __getitem__(self, name):
        return self.columns.has_key(name)

class HTMLRequest:
    ''' The *request*, holding the CGI form and environment.

        "form" the CGI form as a cgi.FieldStorage
        "env" the CGI environment variables
        "base" the base URL for this instance
        "user" a HTMLUser instance for this user
        "classname" the current classname (possibly None)
        "template" the current template (suffix, also possibly None)

        Index args:
        "columns" dictionary of the columns to display in an index page
        "show" a convenience access to columns - request/show/colname will
               be true if the columns should be displayed, false otherwise
        "sort" index sort column (direction, column name)
        "group" index grouping property (direction, column name)
        "filter" properties to filter the index on
        "filterspec" values to filter the index on
        "search_text" text to perform a full-text search on for an index

    '''
    def __init__(self, client):
        self.client = client

        # easier access vars
        self.form = client.form
        self.env = client.env
        self.base = client.base
        self.user = HTMLUser(client, 'user', client.userid)

        # store the current class name and action
        self.classname = client.classname
        self.template = client.template

        self._post_init()

    def _post_init(self):
        ''' Set attributes based on self.form
        '''
        # extract the index display information from the form
        self.columns = []
        if self.form.has_key(':columns'):
            self.columns = handleListCGIValue(self.form[':columns'])
        self.show = ShowDict(self.columns)

        # sorting
        self.sort = (None, None)
        if self.form.has_key(':sort'):
            sort = self.form[':sort'].value
            if sort.startswith('-'):
                self.sort = ('-', sort[1:])
            else:
                self.sort = ('+', sort)
        if self.form.has_key(':sortdir'):
            self.sort = ('-', self.sort[1])

        # grouping
        self.group = (None, None)
        if self.form.has_key(':group'):
            group = self.form[':group'].value
            if group.startswith('-'):
                self.group = ('-', group[1:])
            else:
                self.group = ('+', group)
        if self.form.has_key(':groupdir'):
            self.group = ('-', self.group[1])

        # filtering
        self.filter = []
        if self.form.has_key(':filter'):
            self.filter = handleListCGIValue(self.form[':filter'])
        self.filterspec = {}
        db = self.client.db
        if self.classname is not None:
            props = db.getclass(self.classname).getprops()
            for name in self.filter:
                if self.form.has_key(name):
                    prop = props[name]
                    fv = self.form[name]
                    if (isinstance(prop, hyperdb.Link) or
                            isinstance(prop, hyperdb.Multilink)):
                        self.filterspec[name] = lookupIds(db, prop,
                            handleListCGIValue(fv))
                    else:
                        self.filterspec[name] = fv.value

        # full-text search argument
        self.search_text = None
        if self.form.has_key(':search_text'):
            self.search_text = self.form[':search_text'].value

        # pagination - size and start index
        # figure batch args
        if self.form.has_key(':pagesize'):
            self.pagesize = int(self.form[':pagesize'].value)
        else:
            self.pagesize = 50
        if self.form.has_key(':startwith'):
            self.startwith = int(self.form[':startwith'].value)
        else:
            self.startwith = 0

    def updateFromURL(self, url):
        ''' Parse the URL for query args, and update my attributes using the
            values.
        ''' 
        self.form = {}
        for name, value in cgi.parse_qsl(url):
            if self.form.has_key(name):
                if isinstance(self.form[name], type([])):
                    self.form[name].append(cgi.MiniFieldStorage(name, value))
                else:
                    self.form[name] = [self.form[name],
                        cgi.MiniFieldStorage(name, value)]
            else:
                self.form[name] = cgi.MiniFieldStorage(name, value)
        self._post_init()

    def update(self, kwargs):
        ''' Update my attributes using the keyword args
        '''
        self.__dict__.update(kwargs)
        if kwargs.has_key('columns'):
            self.show = ShowDict(self.columns)

    def description(self):
        ''' Return a description of the request - handle for the page title.
        '''
        s = [self.client.db.config.TRACKER_NAME]
        if self.classname:
            if self.client.nodeid:
                s.append('- %s%s'%(self.classname, self.client.nodeid))
            else:
                if self.template == 'item':
                    s.append('- new %s'%self.classname)
                elif self.template == 'index':
                    s.append('- %s index'%self.classname)
                else:
                    s.append('- %s %s'%(self.classname, self.template))
        else:
            s.append('- home')
        return ' '.join(s)

    def __str__(self):
        d = {}
        d.update(self.__dict__)
        f = ''
        for k in self.form.keys():
            f += '\n      %r=%r'%(k,handleListCGIValue(self.form[k]))
        d['form'] = f
        e = ''
        for k,v in self.env.items():
            e += '\n     %r=%r'%(k, v)
        d['env'] = e
        return '''
form: %(form)s
base: %(base)r
classname: %(classname)r
template: %(template)r
columns: %(columns)r
sort: %(sort)r
group: %(group)r
filter: %(filter)r
search_text: %(search_text)r
pagesize: %(pagesize)r
startwith: %(startwith)r
env: %(env)s
'''%d

    def indexargs_form(self, columns=1, sort=1, group=1, filter=1,
            filterspec=1):
        ''' return the current index args as form elements '''
        l = []
        s = '<input type="hidden" name="%s" value="%s">'
        if columns and self.columns:
            l.append(s%(':columns', ','.join(self.columns)))
        if sort and self.sort[1] is not None:
            if self.sort[0] == '-':
                val = '-'+self.sort[1]
            else:
                val = self.sort[1]
            l.append(s%(':sort', val))
        if group and self.group[1] is not None:
            if self.group[0] == '-':
                val = '-'+self.group[1]
            else:
                val = self.group[1]
            l.append(s%(':group', val))
        if filter and self.filter:
            l.append(s%(':filter', ','.join(self.filter)))
        if filterspec:
            for k,v in self.filterspec.items():
                if type(v) == type([]):
                    l.append(s%(k, ','.join(v)))
                else:
                    l.append(s%(k, v))
        if self.search_text:
            l.append(s%(':search_text', self.search_text))
        l.append(s%(':pagesize', self.pagesize))
        l.append(s%(':startwith', self.startwith))
        return '\n'.join(l)

    def indexargs_url(self, url, args):
        ''' embed the current index args in a URL '''
        l = ['%s=%s'%(k,v) for k,v in args.items()]
        if self.columns and not args.has_key(':columns'):
            l.append(':columns=%s'%(','.join(self.columns)))
        if self.sort[1] is not None and not args.has_key(':sort'):
            if self.sort[0] == '-':
                val = '-'+self.sort[1]
            else:
                val = self.sort[1]
            l.append(':sort=%s'%val)
        if self.group[1] is not None and not args.has_key(':group'):
            if self.group[0] == '-':
                val = '-'+self.group[1]
            else:
                val = self.group[1]
            l.append(':group=%s'%val)
        if self.filter and not args.has_key(':filter'):
            l.append(':filter=%s'%(','.join(self.filter)))
        for k,v in self.filterspec.items():
            if not args.has_key(k):
                if type(v) == type([]):
                    l.append('%s=%s'%(k, ','.join(v)))
                else:
                    l.append('%s=%s'%(k, v))
        if self.search_text and not args.has_key(':search_text'):
            l.append(':search_text=%s'%self.search_text)
        if not args.has_key(':pagesize'):
            l.append(':pagesize=%s'%self.pagesize)
        if not args.has_key(':startwith'):
            l.append(':startwith=%s'%self.startwith)
        return '%s?%s'%(url, '&'.join(l))
    indexargs_href = indexargs_url

    def base_javascript(self):
        return '''
<script language="javascript">
submitted = false;
function submit_once() {
    if (submitted) {
        alert("Your request is being processed.\\nPlease be patient.");
        return 0;
    }
    submitted = true;
    return 1;
}

function help_window(helpurl, width, height) {
    HelpWin = window.open('%s' + helpurl, 'RoundupHelpWindow', 'scrollbars=yes,resizable=yes,toolbar=no,height='+height+',width='+width);
}
</script>
'''%self.base

    def batch(self):
        ''' Return a batch object for results from the "current search"
        '''
        filterspec = self.filterspec
        sort = self.sort
        group = self.group

        # get the list of ids we're batching over
        klass = self.client.db.getclass(self.classname)
        if self.search_text:
            matches = self.client.db.indexer.search(
                re.findall(r'\b\w{2,25}\b', self.search_text), klass)
        else:
            matches = None
        l = klass.filter(matches, filterspec, sort, group)

        # return the batch object, using IDs only
        return Batch(self.client, l, self.pagesize, self.startwith,
            classname=self.classname)

# extend the standard ZTUtils Batch object to remove dependency on
# Acquisition and add a couple of useful methods
class Batch(ZTUtils.Batch):
    ''' Use me to turn a list of items, or item ids of a given class, into a
        series of batches.

        ========= ========================================================
        Parameter  Usage
        ========= ========================================================
        sequence  a list of HTMLItems or item ids
        classname if sequence is a list of ids, this is the class of item
        size      how big to make the sequence.
        start     where to start (0-indexed) in the sequence.
        end       where to end (0-indexed) in the sequence.
        orphan    if the next batch would contain less items than this
                  value, then it is combined with this batch
        overlap   the number of items shared between adjacent batches
        ========= ========================================================

        Attributes: Note that the "start" attribute, unlike the
        argument, is a 1-based index (I know, lame).  "first" is the
        0-based index.  "length" is the actual number of elements in
        the batch.

        "sequence_length" is the length of the original, unbatched, sequence.
    '''
    def __init__(self, client, sequence, size, start, end=0, orphan=0,
            overlap=0, classname=None):
        self.client = client
        self.last_index = self.last_item = None
        self.current_item = None
        self.classname = classname
        self.sequence_length = len(sequence)
        ZTUtils.Batch.__init__(self, sequence, size, start, end, orphan,
            overlap)

    # overwrite so we can late-instantiate the HTMLItem instance
    def __getitem__(self, index):
        if index < 0:
            if index + self.end < self.first: raise IndexError, index
            return self._sequence[index + self.end]
        
        if index >= self.length:
            raise IndexError, index

        # move the last_item along - but only if the fetched index changes
        # (for some reason, index 0 is fetched twice)
        if index != self.last_index:
            self.last_item = self.current_item
            self.last_index = index

        item = self._sequence[index + self.first]
        if self.classname:
            # map the item ids to instances
            if self.classname == 'user':
                item = HTMLUser(self.client, self.classname, item)
            else:
                item = HTMLItem(self.client, self.classname, item)
        self.current_item = item
        return item

    def propchanged(self, property):
        ''' Detect if the property marked as being the group property
            changed in the last iteration fetch
        '''
        if (self.last_item is None or
                self.last_item[property] != self.current_item[property]):
            return 1
        return 0

    # override these 'cos we don't have access to acquisition
    def previous(self):
        if self.start == 1:
            return None
        return Batch(self.client, self._sequence, self._size,
            self.first - self._size + self.overlap, 0, self.orphan,
            self.overlap)

    def next(self):
        try:
            self._sequence[self.end]
        except IndexError:
            return None
        return Batch(self.client, self._sequence, self._size,
            self.end - self.overlap, 0, self.orphan, self.overlap)

class TemplatingUtils:
    ''' Utilities for templating
    '''
    def __init__(self, client):
        self.client = client
    def Batch(self, sequence, size, start, end=0, orphan=0, overlap=0):
        return Batch(self.client, sequence, size, start, end, orphan,
            overlap)

