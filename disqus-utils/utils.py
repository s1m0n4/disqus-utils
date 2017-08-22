# -*- coding: utf-8 -*-
'''
   Created on Dec 9, 2016
   @author: s1m0n4
   @copyright: 2016 s1m0n4
'''
import os

def read_file(f):
    '''
    @return: the file contents if the file exists, otherwise None.
    '''
    result = None
    if os.path.exists(f):
        if os.path.isfile(f):
            with open(f, 'r') as fo:
                result = fo.read()
    return result


def write_file(ifile, contents, mode='w'):
    '''
    Opens a file and writes the contents
    '''
    with open(ifile, mode) as f:
        f.write(contents)
        f.flush()

    return True

