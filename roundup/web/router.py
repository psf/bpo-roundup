#!/usr/bin/env python
"""
The purpose of router is to make Roundup URL scheme configurable
and allow extensions add their own handlers and URLs to tracker.

Public domain work by:
  anatoly techtonik <techtonik@gmail.com>
"""

import re


# --- Example URL mapping

class NamedObject(object):
    """Object that outputs given name when printed"""
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name

ExampleHandler = NamedObject('ExampleHandler')
ExampleFileHandler = NamedObject('ExampleFileHandler')

EXAMPLE_URLMAP = (
    '/static/(.*)', ExampleFileHandler,
    '/', ExampleHandler
)


# --- Regexp based router

class Router(object):

    def __init__(self, urlmap=[]):
        """
        `urlmap` is a list (pattern, handler, pattern, ...)
        """
        self.urlmap = urlmap

    def get_handler(self, urlpath):
        """
        `urlpath` is a part of url /that/looks?like=this

        returns tuple (handler, arguments) or (None, ())
        """
        for i in range(0, len(self.urlmap), 2):
            pattern, handler = self.urlmap[i], self.urlmap[i+1]
            match = re.match(pattern, urlpath)
            if match:
                return handler, match.groups()
        return (None, ())



# [ ] len(urlmap) should be even to avoid errors
#     (find a way to explain this to users)

if __name__ == '__main__':

    import unittest
    class test_Router(unittest.TestCase):
        def test_example_routes(self):
            router = Router(EXAMPLE_URLMAP)
            self.assertEquals(router.get_handler(''), (None, ()))
            handler, params = router.get_handler('/')
            self.assertEquals(handler, ExampleHandler)
            self.assertEquals(params, tuple())

    unittest.main()
