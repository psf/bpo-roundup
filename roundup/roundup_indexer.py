#
# Copyright (c) 2001 Bizar Software Pty Ltd (http://www.bizarsoftware.com.au/)
# This module is free software, and you may redistribute it and/or modify
# under the same terms as Python, so long as this copyright message and
# disclaimer are retained in their original form.
#
# IN NO EVENT SHALL BIZAR SOFTWARE PTY LTD BE LIABLE TO ANY PARTY FOR
# DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES ARISING
# OUT OF THE USE OF THIS CODE, EVEN IF THE AUTHOR HAS BEEN ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# BIZAR SOFTWARE PTY LTD SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING,
# BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE.  THE CODE PROVIDED HEREUNDER IS ON AN "AS IS"
# BASIS, AND THERE IS NO OBLIGATION WHATSOEVER TO PROVIDE MAINTENANCE,
# SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.
# 
#$Id: roundup_indexer.py,v 1.1.2.1 2002-04-03 11:55:57 rochecompaan Exp $
'''
This module provides an indexer class, RoundupIndexer, that stores text
indices in a roundup instance.  This class makes searching the content of
messages and text files possible.
'''
import os
from roundup.indexer import SlicedZPickleIndexer

class RoundupIndexer(SlicedZPickleIndexer):
    ''' Indexes messages and files 
    '''

    def __init__(self, db_path):
        indexdb_path = os.path.join(db_path, 'indexes')
        index_exists = 0
        if not os.path.exists(indexdb_path):
            os.makedirs(indexdb_path)
            os.chmod(indexdb_path, 0775)
            index_exists = 1
        index_path = os.path.join(indexdb_path, 'index.db')
        SlicedZPickleIndexer.__init__(self, 
            INDEXDB=index_path, QUIET=9)
        files_path = os.path.join(db_path, 'files')
        if not index_exists:
            self.add_files(dir=files_path)
            self.save_index()

#
#$Log: not supported by cvs2svn $
