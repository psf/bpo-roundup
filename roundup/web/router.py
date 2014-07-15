#!/usr/bin/env python
"""
The purpose of router is to make Roundup URL scheme configurable
and allow extensions add their own handlers and URLs to tracker.

Public domain work by:
  anatoly techtonik <techtonik@gmail.com>
"""

import re


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
