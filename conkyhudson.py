#!/usr/bin/python

import sys
import getopt
from hudsonstatus import HudsonStatus
import re

def getOutput(template, statuses):
    output = u""
    end = False
    a = 0
        
    # a and b are indexes in the template string
    # moving from left to right the string is processed
    # b is index of the opening bracket and a of the closing bracket
    # everything between b and a is a template that needs to be parsed
    while not end:
        b = template.find('[', a)
        
        if b == -1:
            b = len(template)
            end = True            
        # if there is something between a and b, append it straight to output
        if b > a:
            output += template[a : b]
            # check for the escape char (if we are not at the end)
            if template[b - 1] == '\\' and not end:
                # if its there, replace it by the bracket
                output = output[:-1] + '['
                # skip the bracket in the input string and continue from the beginning
                a = b + 1
                continue
                    
        if end:
            break
            
        a = template.find(']', b)
            
        if a == -1:
            self.logError("Missing terminal bracket (]) for a template item")
            return u""
            
        # if there is some template text...
        if a > b + 1:
            output += parseResultFields(template[b + 1 : a], statuses)
            
        a = a + 1

    return output

    
def getAndRemoveJobs(templateIter, contents):
    """Removes the jobs from the template and gets the info from hudson
    on the job"""
    
    jobs = {}
    charsRemoved = 0
    
    for templateValue in templateIter:
        theString = templateValue.group(1)
        fieldValues = theString.split(";")
        if(fieldValues[0] == "job"):
            status = HudsonStatus(fieldValues[2],fieldValues[3])
            jobs[fieldValues[1]] = status
            contents = contents[0:templateValue.start() - charsRemoved] + contents[templateValue.end()- charsRemoved+1:]
            charsRemoved += templateValue.end() - templateValue.start()+1;
            
    return [jobs, contents]

class TemplateItem:
    """
    Taking in the input from the template, in the form of [job;field;output values]
    and taking in the data from the jobs, return an appropriate string for the output.
    
    This will depend on the type of field in hudsonStatus.
    """
    def __init__(self, text, statuses):
        values = text.split(";")
        self.__jobId = values[0]
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
            if job["building"]:
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
        
    
def parseResultFields(hudsonStatus, statuses):
    item = TemplateItem(hudsonStatus, statuses)
    return str(item)
    
def parseTemplate(contents, baseurl, jobs, showpossible):
    thing = re.finditer("\[(.*?)\]", contents)
    (statuses, template) = getAndRemoveJobs(thing,contents)
    if baseurl is not None and jobs is not None:
        statuses[str(len(statuses.keys())+1)] = HudsonStatus(baseurl, jobs)

    if showpossible:
        key = statuses.keys()[0]
        print "possible keys: ", statuses[key].keys()
        return ""

    final = getOutput(template, statuses)
    
    #print "FINAL CONTENTS ====================\n",final
    #print "DONE =============================="

    return final

def outputBuildStatus(template, baseurl, jobs, showpossible):
    f=open(template)
    contents = f.read()
    templateValues = parseTemplate(contents, baseurl, jobs, showpossible)
    
    if len(templateValues) > 0:
        print templateValues

def main(argv):
    import optparse
    parser = optparse.OptionParser("usage: %prog <options>",
                                   None, optparse.Option, "0.2", 'error')
    parser.add_option("-t", "--template", dest="template", default=None)
    parser.add_option("-b", "--baseurl", dest="baseurl", default=None)
    parser.add_option("-j", "--jobs", dest="jobs", default=None)
    parser.add_option("", "--showpossible", dest="showpossible", action="store_true")
    (options, args) = parser.parse_args()

    if options.template is None:
        parser.error("Failed to specify the template")

    outputBuildStatus(options.template, options.baseurl, options.jobs, showpossible=options.showpossible)
    
    
if __name__ == "__main__":
    main(sys.argv[1:])
