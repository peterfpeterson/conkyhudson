#!/usr/bin/python

import urllib2
import sys
import getopt
class HudsonStatus:
    
    urlString = '%s/job/%s/lastBuild/api/python'

    def __init__(self, baseurl, name, debug=False):
        self.__urlString = self.urlString % (baseurl, name)
        if debug:
            print "URL:", self__urlString
        self.__rawJob = eval(urllib2.urlopen(self.__urlString, timeout=2).read())
        
    def __repr__(self):
        return "HudsonStatus(%s)" % self.__urlString

    def keys(self):
        return self.__rawJob.keys()[:]

    def __getitem__(self, name):
        #print "__getitem__(%s)" % name
        if name in self.keys():
            return self.__rawJob[name]
        else:
            raise KeyError(name + " is not a valid key")
