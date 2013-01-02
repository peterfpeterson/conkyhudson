#!/usr/bin/python

import urllib2
import os
import sys
import getopt
class HudsonStatus:
    def __init__(self, baseurl, name, buildurlext, debug=0):
        self.__urlString = '/'.join([baseurl, 'job', name, buildurlext, 'api/python'])
        if debug:
            print "URL:", self.__urlString

        self.__rawJob = eval(urllib2.urlopen(self.__urlString, timeout=2).read())
        
    def __repr__(self):
        return "HudsonStatus(%s)" % self.__urlString

    def keys(self):
        return self.__rawJob.keys()[:]

    def __getitem__(self, name):
        #print "__getitem__('%s')" % name
        if name in self.keys():
            return self.__rawJob[name]
        else:
            raise KeyError(name + " is not a valid key")
