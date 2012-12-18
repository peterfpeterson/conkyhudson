#!/usr/bin/python

import urllib2
import sys
import getopt
class HudsonStatus:
    
    urlString = '%s/job/%s/lastBuild/api/python'

   
    def getUrl(self,baseurl,job):
        return self.urlString % (baseurl, job)
        
    def getBuildStatus(self,baseurl, job):
        url = self.getUrl(baseurl,job)
        #print "URL:" + url
        hudsonJob = eval(urllib2.urlopen(url, timeout=2).read())
        return hudsonJob
        
        
    
    
