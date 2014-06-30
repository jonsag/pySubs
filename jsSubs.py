#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

# edit .conf to suit your needs

# options:
# -p <path> scan single path
# -r <path> scan path recursively
# -s <suffix> file suffix to search for

#import sys, getopt, os
import getopt

from myFunctions import *

##### set config file #####
#config = configparser.ConfigParser()
#config.sections()
#config.read('setSubLang.ini') # read config file

##### handle arguments #####
try:
    myopts, args = getopt.getopt(sys.argv[1:],'p:r:s:dg', ['path=', 'recursive=', 'suffix=', 'detectlang', 'get'])

except getopt.GetoptError as e:
    print "\n%s" % (str(e))
    usage(2) # print usage and exit with code

for o, a in myopts:
    if o in ('-p', '--path'):
        searchPath = a
        programPart = "scan"
    elif o in ('-r', '--recursive'):
        searchPathRecursive = a
        programPart = "scan"
    elif o in ('-s', '--suffix'):
        suffix = a
    elif o in ('-d', '--detectlang'):
        programPart = "status"
    elif o in ('-g', '--get'):
        programPart = "get"
    else:
        print "\nError: Wrong set of arguments passed"
        usage(6)

if len(sys.argv) == 1: # no arguments passed
    print "\nNo path given."
    print "Using current dir"
    recursive = ""
    searchPath = "%s/" % os.getcwd() # current dir                                                                                                                              
    suffix = ".srt"
    programPart = "scan"

elif programPart == "scan": # argument -r or -p passed
    if not searchPathRecursive and not searchPath: # check that a path is given
        print "\nError: No search path given!"
        usage(3) # print usage and exit with code
    if searchPathRecursive and searchPath: # check that only one path is given
        print "\nError: You can't state both path and recursive path!"
        usage(4) # print usage and exit with code
    if searchPathRecursive: # -r recursive path given
        if not os.path.isdir(searchPathRecursive): # not a valid path
            print "\nError: %s is not a valid path!" % searchPathRecursive
            sys.exit(6)
        else:
            searchPath = searchPathRecursive
            recursive = " recursively"
    elif searchPath: # -p path given
        if not os.path.isdir(searchPath): # not a valid path
            print "\nError: %s is not a valid path!" % searchPath
            sys.exit(6)
        else:
            recursive = ""

    if not suffix: # suffix not given
        print "\nNo suffix given!"
        print "Setting srt"
        suffix = ".srt"
    else:
        suffix = ".%s" % suffix.lstrip('.') # remove leading . if any

########################################## scan ##########################################
if programPart == "scan":
    print "\nSearching %s%s for files ending with %s" % (searchPath, recursive, suffix)
    
    # scan directories recursively
    if searchPathRecursive:
        for root, dirs, files in os.walk(searchPath):
            for file in files:
                if isFile(os.path.join(root, file), suffix):
                    langSums = fileFound(os.path.join(root, file), langSums)
                    num += 1

    # scan single directory
    if searchPath:
        for file in os.listdir(searchPath):
            if isFile(file, suffix):
                langSums = fileFound(file, langSums)
                num += 1

    print "\nNumber of %s files in %s: %d\n" % (suffix, searchPath, num)

    print "Languages found:"
    for lang in languages:
        langSum = langSums.count(lang['code'])
        if langSums.count(lang['code']) > 0:
            print "%s - %s:  %d" % (lang['code'], lang['name'].lower(), langSum)
    print "\n"

########################################## status ##########################################
elif programPart == "status":
    print "\nAvailable languages:"
    print "-------------------------------------------------------------------------------------"
    for language in languages:
        print "%s %s" %(language['code'], language['name'])

    print "\n%d available languages" % len(languages)

    status = detectlanguage.user_status()

    print "\ndetectlanguage.com status for API-key: %s" % detectlanguage.configuration.api_key
    print "-------------------------------------------------------------------------------------"
    print "Status: %s" %status['status']
    print "Account type/plan: %s" % status['plan']
    print "\nTodays date: %s" % status['date']
    print "Plan expires: %s" % status['plan_expires']
    print '\nRequest: %d / %d' % (status['requests'], status['daily_requests_limit'])
    print 'Bytes: %d / %d' % (status['bytes'], status['daily_bytes_limit'])
    
########################################## get ##########################################
elif programPart == "get":
    if not searchPath:
        print "\nNo path given."
        print "Using current dir"
        searchPath = "%s/" % os.getcwd() # current dir

    print "\nSearching %s for video files" % searchPath

    for file in os.listdir(searchPath):
        videoFound = False
        for suffix in videoSuffixes:
            if isVideo(file, suffix):
                print "\n%s" % file
                num += 1
                videoFound = True
                break
        if videoFound:
            subDownloads = hasSub(file)

    print "\nNumber of video files in %s: %d\n" % (searchPath, num)

    print "Downloaded subtitles:"
    for lang in prefLangs:
        sub = subDownloads.count(lang)
        print "%s - %s:  %d" % (lang, langName(lang).lower(), sub)

    print "\nMissing but not found:"
    for lang in prefLangs:
        sub = subDownloads.count("%s - not found" % lang)
        print "%s - %s:  %d" % (lang, langName(lang).lower(), sub)

    print "\nSubtitles present:"
    for lang in prefLangs:
        sub = subDownloads.count("%s - present" % lang)
        print "%s - %s:  %d" % (lang, langName(lang).lower(), sub)

    print "\n"
