#!/usr/bin/python

import sys
import getopt
from hudsonstatus import HudsonStatus
import re

DEFAULT_URL_EXT = "lastBuild"

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
            "ERROR":"ERROR",       # option 4
            "ABORTED":"ABORTED"    # option 5
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
                            if num > 5:
                                status["ABORTED"]    = options[5]

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

    def __processHeathReportField(self):
        statusType = 'Build' # other option is 'Test'
        statusKey = 'score'
        if not self.__options is None:
            temp = self.__options.split(",")
            statusType = temp[0]
            if len(temp) > 1:
                statusKey = temp[1]

        # update to the correct status type
        status = None
        for item in self.__status[self.__name]:
            if item['description'].startswith(statusType):
                status = item
                break

        return str(status[statusKey])+"%"

    def __processBuildableField(self):
        options = ['active', 'disabled']
        if not self.__options is None:
            temp = self.__options.split(',')
            for i in range(len(temp)):
                options[i] = temp[i]

        result = bool(self.__status[self.__name])
        if result:
            return options[0]
        else:
            return options[1]

    def __str__(self):
        if(self.__name == "result"):
            return self.__processResultField()
        elif(self.__name == "culprit"):
            return self.__processCulpritField()
        elif(self.__name == "healthReport"):
            return self.__processHeathReportField()
        elif(self.__name == "buildable"):
            return self.__processBuildableField()
        else: #if it doesn't match anything, just attempt to return it's value
            return str(self.__status[self.__name])
        
class TemplateFile:
    def __init__(self, filename, debug=0):
        self.debug = debug
        # read the file
        f=open(filename)
        self.contents = f.read()
        f.close()

        self.__lastBaseUrl = None
        
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

            jobNum = int(fieldValues[1])

            # make sure that there is something to do
            numValues = len(fieldValues)
            if numValues < 3:
                raise RuntimeError("Did not specify enough information for the job. Only %d fields found" % numValues)
            self.__lastBaseUrl = fieldValues[2]

            # add the specified job as appropriate
            if numValues > 3:
                jobs = fieldValues[3]
                if numValues > 4: # everything else is trash
                    urlexts = fieldValues[4]
                else:
                    urlexts = DEFAULT_URL_EXT

                self.__jobDescr[jobNum] = (self.__lastBaseUrl, jobs, urlexts)

            # strip off the extra values
            self.contents = self.contents.replace(templateValue.group(0), '')

    def addJobs(self, baseurl, jobs, buildurlexts):
        """Add an extra one specified on the command line.
        Multiple jobs at the same url are comma separated."""
        if self.debug > 1:
            print "addJobs('%s', '%s', '%s')" % (baseurl, jobs, buildurlexts)
        if baseurl is None:
            baseurl = self.__lastBaseUrl
        if jobs is None:
            if self.debug > 0:
                print "in addJobs: no job was specified"
            return

        # determine the key
        if len(self.__jobDescr.keys()) <= 0:
            key = 1
        else:
            key = max(self.__jobDescr.keys()) + 1

        for job in jobs.split(','):
            for ext in buildurlexts.split(','):
                self.__jobDescr[key] = (baseurl, job, ext)
                key += 1

    def keys(self):
        return self.__jobDescr.keys()

    def descr(self, key):
        key = int(key)
        return self.__jobDescr[key]

    def numJobs(self):
        return len(self.__jobDescr)

    def getStatus(self, key):
        (baseurl, job, buildurlext) = self.descr(key)
        if baseurl is None:
            raise RuntimeError("Failed to specify base url")
        if job is None:
            raise RuntimeError("Failed to specify job name")
        if buildurlext is None:
            buildurlext = DEFAULT_URL_EXT # default to reasonable value
        #print "getStatus(%s) : %s" %(key, self.descr(key))
        return HudsonStatus(baseurl, job, buildurlext, debug=(self.debug>0))

    def getFirstStatus(self):
        key = self.__jobDescr.keys()[0]
        return self.getStatus(key)

def main(argv):
    import optparse
    parser = optparse.OptionParser("usage: %prog <options>",
                                   None, optparse.Option, "0.2", 'error')
    parser.add_option("-t", "--template", dest="template", default=None)
    parser.add_option("-b", "--baseurl", dest="baseurl", default=None)
    parser.add_option("-e", "--buildurlext", dest="buildurlext", default=DEFAULT_URL_EXT)
    parser.add_option("-j", "--jobs", dest="jobs", default=None)
    parser.add_option("", "--showpossible", dest="showpossible", action="store_true")
    parser.add_option("-d", "--debug", dest="debug", default=0, action="count")
    (options, args) = parser.parse_args()

    # template file is required
    if options.template is None:
        parser.error("Failed to specify the template")

    # parse the template
    template = TemplateFile(options.template, options.debug)
    template.addJobs(options.baseurl, options.jobs, options.buildurlext)
    if template.numJobs() <= 0:
        parser.error("Failed to specify any jobs")

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
