#!/usr/bin/env python
# This Router component was written by techtonik@gmail.com and it's been
# placed in the Public Domain. Copy and modify to your heart's content.

"""
The purpose of router is to make Roundup URL scheme configurable
and allow extensions add their own handlers and URLs to tracker.
"""

DEBUG = False


import re

# --- Example URL mapping

class NamedObject(object):
    """Object that outputs its name when printed"""
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name

ExampleHandler = NamedObject('ExampleHandler')
ExampleFileHandler = NamedObject('ExampleFileHandler')


EXAMPLE_URL_MAP = (
    'static/(.*)', ExampleFileHandler,
    'index', ExampleHandler
)


# --- Regexp based router

class Router(object):

    def __init__(self, urlmap=[]):
        """
        `urlmap` is a list (pattern, handler, pattern, ...)
        leading slash in pattern is stripped
        """
        self.urlmap = urlmap

    def get_handler(self, urlpath):
        """
        `urlpath` is a part of url /that/looks?like=this
        (leading slash is optional, will be stripped anyway)

        returns tuple (handler, arguments) or (None, ())
        """
        # strip leading slashes before matching
        path = urlpath.lstrip('/')
        for i in range(0, len(self.urlmap), 2):
            pattern, handler = self.urlmap[i], self.urlmap[i+1]
            pattern = pattern.lstrip('/')
            if DEBUG:
                print('router: matching %s' % pattern)
            match = re.match(pattern, path)
            if match:
                return handler, match.groups()
        return (None, ())



# [ ] len(urlmap) should be even to avoid errors
#     (find a way to explain this to users)

if __name__ == '__main__':

    import unittest
    class test_Router(unittest.TestCase):
        def test_example_routes(self):
            router = Router(EXAMPLE_URL_MAP)
            self.assertEquals(router.get_handler(''), (None, ()))
            handler, params = router.get_handler('/index')
            self.assertEquals(handler, ExampleHandler)
            self.assertEquals(params, tuple())

        def test_route_param(self):
            def echo_handler(args):
                return args
            router = Router(('/files/(.*)', echo_handler))
            self.assertEquals(router.get_handler(''), (None, ()))
            self.assertEquals(router.get_handler('/files'), (None, ()))
            handler, params = router.get_handler('/files/filename')
            self.assertEquals(handler, echo_handler)
            self.assertEquals(params, ('filename',))

    unittest.main()
