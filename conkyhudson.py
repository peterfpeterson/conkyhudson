#!/usr/bin/python

import sys
import getopt
from hudsonstatus import HudsonStatus
import re

def fillTemplate(contents, statuses):
    templateIter = re.finditer("\[(.*?)\]", contents)
    for templateValue in templateIter:
        expanded = TemplateItem(templateValue.group(1), statuses)
        contents = contents.replace(templateValue.group(0), str(expanded))

    return contents

class TemplateItem:
    """
    Taking in the input from the template, in the form of [job;field;output values]
    and taking in the data from the jobs, return an appropriate string for the output.
    
    This will depend on the type of field in hudsonStatus.
    """
    def __init__(self, text, statuses):
        values = text.split(";")
        self.__jobId = int(values[0])
        self.__name = values[1]
        self.__options = None
        if len(values) > 2:
            self.__options = values[2]
        self.__status = statuses[self.__jobId]

    def __processResultField(self):
        """Process the 'result' field """

        # default outputs
        status = {
            "SUCCESS":"SUCCESS",   # option 0
            "FAILURE":"FAILURE",   # option 1
            "BUILDING":"BUILDING", # option 2
            "UNSTABLE":"UNSTABLE", # option 3
            "ERROR":"ERROR"        # option 4
            }
        # parse the options
        if not self.__options is None:
            options = self.__options.split(",")
            num = len(options)
            status["SUCCESS"]  = options[0]
            if num > 1:
                status["FAILURE"]  = options[1]
                if num > 2:
                    status["BUILDING"] = options[2]
                    if num > 3:
                        status["UNSTABLE"] = options[3]
                        if num > 4:
                            status["ERROR"]    = options[4]

        def format(status): # inner method for adding percentage
            if '%' in status:
                percent = float(self.__status['duration'])/float(self.__status['estimatedDuration'])
                return status % percent
            else:
                return status

        # conver the status to a string
        result = self.__status["result"]
        if result is None:
            if self.__status["building"]:
                return format(status["BUILDING"])
            else:
                return format(status["ERROR"])
        else:
            return format(status[result])
        
    def __processCulpritField(self):
        """Process the 'culprit' field"""
    
        # set the default value if not specified
        default = self.__options
        if default is None:
            default = "unknown"

        # get the list of culprits
        rawCulprits = self.__status["culprits"]
        if(rawCulprits == None):
            return default

        # convert them to their full names
        culprits = []
        for culprit in rawCulprits:
            if len(culprit["fullName"]):
                culprits.append(culprit["fullName"])

        # return a comma separated list
        if len(culprits) > 0:
            return ', '.join(culprits)
        else:
            return default

    def __str__(self):
        if(self.__name == "result"):
            return self.__processResultField()
        elif(self.__name == "culprit"):
            return self.__processCulpritField()
        else: #if it doesn't match anything, just attempt to return it's value
            return self.__status[self.__name]
        
class TemplateFile:
    def __init__(self, filename):
        # read the file
        f=open(filename)
        self.contents = f.read()
        f.close()
        
        # parse the template
        self.__getAndRemoveJobs()

    def __getAndRemoveJobs(self):
        """Removes the jobs from the template and gets the info from hudson
        on the job"""
    
        self.__jobDescr = {} # description of the jobs as (baseurl, name)
        templateIter = re.finditer("\[(job.*?)\]\\s+", self.contents)
        for templateValue in templateIter:
            theString = templateValue.group(1)
            fieldValues = theString.split(";")
            self.__jobDescr[int(fieldValues[1])] = (fieldValues[2],fieldValues[3]) # last one wins
            self.contents = self.contents.replace(templateValue.group(0), '')

    def addJobs(self, baseurl, jobs):
        """Add an extra one specified on the command line.
        Multiple jobs at the same url are comma separated."""
        if baseurl is None:
            return
        if jobs is None:
            return

        # determine the key
        if len(self.__jobDescr.keys()) <= 0:
            key = 1
        else:
            key = max(self.__jobDescr.keys()) + 1

        jobs = jobs.split(',')
        for job in jobs:
            self.__jobDescr[key] = (baseurl, job)
            key += 1

    def keys(self):
        return self.__jobDescr.keys()

    def descr(self, key):
        key = int(key)
        return self.__jobDescr[key]

    def getStatus(self, key):
        (baseurl, job) = self.descr(key)
        return HudsonStatus(baseurl, job)

    def getFirstStatus(self):
        key = self.__jobDescr.keys()[0]
        return self.getStatus(key)

def main(argv):
    import optparse
    parser = optparse.OptionParser("usage: %prog <options>",
                                   None, optparse.Option, "0.2", 'error')
    parser.add_option("-t", "--template", dest="template", default=None)
    parser.add_option("-b", "--baseurl", dest="baseurl", default=None)
    parser.add_option("-j", "--jobs", dest="jobs", default=None)
    parser.add_option("", "--showpossible", dest="showpossible", action="store_true")
    (options, args) = parser.parse_args()

    # template file is required
    if options.template is None:
        parser.error("Failed to specify the template")

    # parse the template
    template = TemplateFile(options.template)
    template.addJobs(options.baseurl, options.jobs)

    # skip out early
    if options.showpossible:
        status = template.getFirstStatus()
        print "possible keys: ", status.keys()
        return

    # convert the job descriptions into statuses
    statuses = {}
    for key in template.keys():
        statuses[key] = template.getStatus(key)

    # do all of the formatting
    final = fillTemplate(template.contents, statuses)
    if len(final) > 0:
        print final

if __name__ == "__main__":
    main(sys.argv[1:])
