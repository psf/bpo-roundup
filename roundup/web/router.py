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

# --- Helper functions

def entry(prompt='> '):
    """Just get text for interactive mode"""
    import sys
    if sys.version_info[0] < 3:
        return raw_input(prompt)
    else:
        return input(prompt)

# --- Regexp based router

class Router(object):

    urlmap = []

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
        for pattern, handler in self.iter_urlmap():
            pattern = pattern.lstrip('/')
            if DEBUG:
                print('router: matching %s' % pattern)
            match = re.match(pattern, path)
            if match:
                return handler, match.groups()
        return (None, ())

    def iter_urlmap(self):
        """
        iterate over self.urlmap returning (pattern, handler) pairs
        """
        for i in range(0, len(self.urlmap), 2):
            yield self.urlmap[i], self.urlmap[i+1]

    def interactive(self):
        print('enter url to test, [l] to list rules, empty line exits')
        url = entry('url: ')
        while url != '':
            if url == 'l':
                for i in range(0, len(self.urlmap), 2):
                    pattern, handler = self.urlmap[i], self.urlmap[i+1]
                    print(self.urlmap[i:i+2])
            print('matched ' + str(self.get_handler(url)))
            url = entry('url: ')


# [ ] len(urlmap) should be even to avoid errors
#     (find a way to explain this to users)

if __name__ == '__main__':

    import sys
    if '-i' in sys.argv:
        router = Router(EXAMPLE_URL_MAP)
        router.interactive()
        sys.exit()

    import unittest
    class test_Router(unittest.TestCase):
        def test_example_routes(self):
            router = Router(EXAMPLE_URL_MAP)
            self.assertEqual(router.get_handler(''), (None, ()))
            handler, params = router.get_handler('/index')
            self.assertEqual(handler, ExampleHandler)
            self.assertEqual(params, tuple())

        def test_route_param(self):
            def echo_handler(args):
                return args
            router = Router(('/files/(.*)', echo_handler))
            self.assertEqual(router.get_handler(''), (None, ()))
            self.assertEqual(router.get_handler('/files'), (None, ()))
            handler, params = router.get_handler('/files/filename')
            self.assertEqual(handler, echo_handler)
            self.assertEqual(params, ('filename',))

    unittest.main()
