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
    myopts, args = getopt.getopt(sys.argv[1:],'p:rs:ldgh', ['path=', 'recursive', 'suffix=', 'link', 'detectlang', 'get', 'help'])

except getopt.GetoptError as e:
    print "\n%s" % (str(e))
    usage(2) # print usage and exit with code

recursive = False
suffix = ".srt"
programPart = ""
searchPath = "%s" % os.getcwd()

if len(sys.argv) == 1: # no optionss passed
    print "\nError: No options given"
    usage(1)

for option, argument in myopts:
    if option in ('-p', '--path'):
        searchPath = "%s/%s" % (os.getcwd(), argument)
    elif option in ('-r', '--recursive'):
        recursive = True
    elif option in ('-s', '--suffix'):
        suffix = argument
    elif option in ('-l', '--link'):
        programPart = "link"
    elif option in ('-d', '--detectlang'):
        programPart = "status"
    elif option in ('-g', '--get'):
        programPart = "get"
    elif option in ('-h', '--help'):
        usage(0)

if len(sys.argv) == 1: # no arguments passed
    print "\nNo path given."
    print "Linking current dir"
    searchPath = "%s/" % os.getcwd() # current dir                                                                                                                              
    programPart = "link"

if not programPart:
    print "\nError: No program part chosen"
    usage(1)

if searchPath: # argument -p --path passed
    if not os.path.isdir(searchPath): # not a valid path
        print "\nError: %s is not a valid path!" % searchPath
        sys.exit(6)
else:
    print "\nNo path given."
    print "Using current dir"

if suffix: # argument -s --suffix passed
    suffix = ".%s" % suffix.lstrip('.') # remove leading . if any
else:
    print "\nNo suffix given!"
    print "Setting %s" % suffix.lstrip('.') # remove leading . if any

########################################## link ##########################################
if programPart == "link":

    if recursive: # scan directories recursively
        print "\nSearching %s recursively for files ending with %s" % (searchPath, suffix)
        for root, dirs, files in os.walk(searchPath):
            for file in files:
                if isFile(os.path.join(root, file), suffix):
                    langSums = fileFound(os.path.join(root, file), langSums)
                    num += 1

    else: # scan single directory
        print "\nSearching %s for files ending with %s" % (searchPath, suffix)
        for file in os.listdir(searchPath):
            print file
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