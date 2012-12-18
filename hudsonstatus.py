#!/usr/bin/python

import urllib2
import sys
import getopt
class HudsonStatus:
    
    urlString = 'http://%s/job/%s/lastBuild/api/python'

   
    def getUrl(self,server,job):
        return self.urlString % (server, job)
        
    def getBuildStatus(self,server, job):
        url = self.getUrl(server,job)
        #print "URL:" + url
        hudsonJob = eval(urllib2.urlopen(url, timeout=2).read())
        return hudsonJob
        
        
    
    
