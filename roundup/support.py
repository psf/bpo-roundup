"""Implements various support classes and functions used in a number of
places in Roundup code.
"""

__docformat__ = 'restructuredtext'

import os, time, sys
import hyperdb

class TruthDict:
    '''Returns True for valid keys, False for others.
    '''
    def __init__(self, keys):
        if keys:
            self.keys = {}
            for col in keys:
                self.keys[col] = 1
        else:
            self.__getitem__ = lambda name: 1

    def __getitem__(self, name):
        return self.keys.has_key(name)

def ensureParentsExist(dest):
    if not os.path.exists(os.path.dirname(dest)):
        os.makedirs(os.path.dirname(dest))

class PrioList:
    '''Manages a sorted list.

    Currently only implements method 'append' and iteration from a
    full list interface.
    Implementation: We manage a "sorted" status and sort on demand.
    Appending to the list will require re-sorting before use.
    >>> p = PrioList ()
    >>> for i in 5,7,1,-1 :
    ...  p.append (i)
    ...
    >>> for k in p :
    ...  print k
    ...
    -1
    1
    5
    7

    '''
    def __init__(self):
        self.list   = []
        self.sorted = True

    def append(self, item):
        self.list.append (item)
        self.sorted = False

    def __iter__(self):
        if not self.sorted :
            self.list.sort ()
            self.sorted = True
        return iter (self.list)

class Progress:
    '''Progress display for console applications.

    See __main__ block at end of file for sample usage.
    '''
    def __init__(self, info, sequence):
        self.info = info
        self.sequence = iter(sequence)
        self.total = len(sequence)
        self.start = self.now = time.time()
        self.num = 0
        self.stepsize = self.total / 100 or 1
        self.steptimes = []
        self.display()

    def __iter__(self): return self

    def next(self):
        self.num += 1

        if self.num > self.total:
            print self.info, 'done', ' '*(75-len(self.info)-6)
            sys.stdout.flush()
            return self.sequence.next()

        if self.num % self.stepsize:
            return self.sequence.next()

        self.display()
        return self.sequence.next()

    def display(self):
        # figure how long we've spent - guess how long to go
        now = time.time()
        steptime = now - self.now
        self.steptimes.insert(0, steptime)
        if len(self.steptimes) > 5:
            self.steptimes.pop()
        steptime = sum(self.steptimes) / len(self.steptimes)
        self.now = now
        eta = steptime * ((self.total - self.num)/self.stepsize)

        # tell it like it is (or might be)
        if now - self.start > 3:
            M = eta / 60
            H = M / 60
            M = M % 60
            S = eta % 60
            if self.total:
                s = '%s %2d%% (ETA %02d:%02d:%02d)'%(self.info,
                    self.num * 100. / self.total, H, M, S)
            else:
                s = '%s 0%% (ETA %02d:%02d:%02d)'%(self.info, H, M, S)
        elif self.total:
            s = '%s %2d%%'%(self.info, self.num * 100. / self.total)
        else:
            s = '%s %d done'%(self.info, self.num)
        sys.stdout.write(s + ' '*(75-len(s)) + '\r')
        sys.stdout.flush()

class Proptree :
    ''' Simple tree data structure for optimizing searching of properties
    '''

    def __init__ (self, db, cls, name, props, parent = None, val = None) :
        self.db        = db
        self.name      = name
        self.props     = props
        self.parent    = parent
        self.val       = val
        self.cls       = cls
        self.classname = None
        self.uniqname  = None
        self.children  = []
        self.propnames = {}
        if parent :
            self.root  = parent.root
            self.prcls = self.parent.props [name]
        else :
            self.root  = self
            self.seqno = 1
        self.id = self.root.seqno
        self.root.seqno += 1
        if self.cls :
            self.classname = self.cls.classname
            self.uniqname  = '%s%s' % (self.cls.classname, self.id)
        if not self.parent :
            self.uniqname  = self.cls.classname

    def append (self, name) :
        if name in self.propnames :
            return self.propnames [name]
        propclass = self.props [name]
        cls   = None
        props = None
        if isinstance (propclass, (hyperdb.Link, hyperdb.Multilink)) :
            cls   = self.db.getclass (propclass.classname)
            props = cls.getprops ()
        child = self.__class__ (self.db, cls, name, props, parent = self)
        self.children.append (child)
        self.propnames [name] = child
        return child

    def __iter__ (self) :
        """ Yield nodes in depth-first order -- visited nodes first """
        for p in self.children :
            yield p
            for c in p :
                yield c

# vim: set et sts=4 sw=4 :
