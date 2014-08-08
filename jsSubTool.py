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
    myopts, args = getopt.getopt(sys.argv[1:],'p:rs:ldgc:fhv' , ['path=', 'recursive', 'suffix=', 'link', 'detectlang', 'get', 'check=', 'format', 'help', 'verbose'])

except getopt.GetoptError as e:
    onError(1, str(e))

recursive = False
suffix = ".srt"
searchPath = os.path.abspath(os.getcwd())
doLink = False
doStatus = False
doGet = False
doCheck = False
doFormat = False
verbose = False
findCode = ""

if len(sys.argv) == 1: # no options passed
    onError(2, 2)

for option, argument in myopts:
    if option in ('-p', '--path'):
        searchPath = os.path.abspath(argument)
    elif option in ('-r', '--recursive'):
        recursive = True
    elif option in ('-s', '--suffix'):
        suffix = argument
    elif option in ('-l', '--link'):
        doLink = True
    elif option in ('-d', '--detectlang'):
        doStatus = True
    elif option in ('-g', '--get'):
        doGet = True
    elif option in ('-h', '--help'):
        usage(0)
    elif option in ('-c', '--check'):
        doCheck = True
        if argument == "all" or argument == "pref":
            findCode = argument
        else:
            for language in languages:
                if argument == language['code']:
                    findCode = argument
        if not findCode:
            onError(6, argument)
    elif option in ('-f', '--format'):
        doFormat = True
    elif option in ('-v', '--verbose'):
        verbose = True

if not doLink and not doStatus and not doGet and not doCheck and not doFormat: # no program part selected
    onError(3, 3)

if searchPath: # argument -p --path passed
    if not os.path.isdir(searchPath): # not a valid path
        onError(4, searchPath)
else:
    print "\nNo path given."
    print "Using current dir %s" % searchPath

if suffix: # argument -s --suffix passed
    suffix = ".%s" % suffix.lstrip('.') # remove leading . if any
else:
    print "\nNo suffix given!"
    print "Setting %s" % suffix.lstrip('.') # remove leading . if any

########################################## link ##########################################
def partLink(recursive, searchPath, suffix):
    langSums = []
    num = 0

    if recursive: # scan directories recursively
        print "\nSearching %s recursively for files ending with %s" % (searchPath, suffix)
        for root, dirs, files in os.walk(searchPath):
            for file in files:
                if isFile(os.path.join(root, file), suffix): # check if file matches criteria
                    print "\n%s" % os.path.join(root, file)
                    langSums = fileFound(os.path.join(root, file), langSums, verbose) # go ahead with the file
                    num += 1

    else: # scan single directory
        print "\nSearching %s for files ending with %s" % (searchPath, suffix)
        for file in os.listdir(searchPath):
            if isFile(os.path.join(searchPath, file), suffix): # check if file matches criteria
                print "\n%s" % file
                langSums = fileFound(os.path.join(searchPath, file), langSums, verbose) # go ahead with the file
                num += 1

    print "\nNumber of %s files in %s: %d\n" % (suffix, searchPath, num)

    print "Languages found:"
    for lang in languages:
        langSum = langSums.count(lang['code'])
        if langSums.count(lang['code']) > 0:
            print "%s - %s:  %d" % (lang['code'], lang['name'].lower(), langSum)
    print "\n"

########################################## status ##########################################
def partStatus():
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
def partGet(searchPath):
    subDownloads = []
    num = 0

    if recursive: # scan directories recursively
        print "\nSearching %s recursively for video files" % searchPath
        for root, dirs, files in os.walk(searchPath):
            for file in files:
                videoFound = False
                for suffix in videoSuffixes:
                    if isVideo(os.path.join(str(root), file), suffix): # check if file matches any of the video suffixes
                        print "\n%s" % os.path.join(str(root), file)
                        num += 1
                        videoFound = True
                        break
                if videoFound:
                    subDownloads = hasSub(os.path.join(str(root), file), searchPath) # go ahead processing the video file
    else:
        print "\nSearching %s for video files" % searchPath
        for file in os.listdir(searchPath):
            videoFound = False
            for suffix in videoSuffixes:
                if isVideo(file, suffix): # check if file matches any of the video suffixes
                    print "\n%s" % file
                    num += 1
                    videoFound = True
                    break
            if videoFound:
                subDownloads = hasSub(file, searchPath) # go ahead processing the video file

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

########################################## check ##########################################
def partCheck(recursive, searchPath, suffix, findCode):
    langSums = []
    num = 0

    if recursive: # scan directories recursively
        print "\nSearching %s recursively for files ending with %s" % (searchPath, suffix)
        if findCode:
            print "with language code %s" % findCode
        for root, dirs, files in os.walk(searchPath):
            for file in files:
                if isFile(os.path.join(root, file), suffix): # check if file matches criteria
                    existingCode = hasLangCode(os.path.join(searchPath, file))
                    if existingCode:
                        if findCode:
                            if existingCode['code'] == str(findCode):
                                print "\n%s" % os.path.join(root, file)
                                print "--- Has language code %s - %s" % (existingCode['code'], existingCode['name'].lower())
                                checkedCode = checkLang(os.path.join(root, file), 1) # let detectlanguage.com see what language the file has
                                compareCodes(existingCode['code'], checkedCode, os.path.join(str(root), file))
                                num += 1
                        else:
                            if existingCode:
                                print "\n%s" % os.path.join(root, file)
                                print "--- Has language code %s - %s" % (existingCode['code'], existingCode['name'].lower())
                                checkedCode = checkLang(os.path.join(root, file), 1) # let detectlanguage.com see what language the file has
                                compareCodes(existingCode['code'], checkedCode, os.path.join(str(root), file)) # compare existing and checked code
                                num += 1
                            else:
                                print "*** Has no language code"
  
    else: # scan single directory
        print "\nSearching %s for files ending with %s" % (searchPath, suffix)
        if findCode:
            print "with language code %s" % findCode
        for file in os.listdir(searchPath):
            if isFile(os.path.join(searchPath, file), suffix): # check if file matches criteria
                print "\n%s" % file
                existingCode = hasLangCode(os.path.join(searchPath, file))
                if existingCode:
                    print "--- Has language code %s - %s" % (existingCode['code'], existingCode['name'].lower())
                    checkedCode = checkLang(file, 1)  # let detectlanguage.com see what language the file has

                    compareCodes(existingCode['code'], checkedCode, file)

                    num += 1
                else:
                    print "*** Has no language code"

    print "\nNumber of %s files in %s: %d\n" % (suffix, searchPath, num)

    print "Languages found:"
    for lang in languages:
        langSum = langSums.count(lang['code'])
        if langSums.count(lang['code']) > 0:
            print "%s - %s:  %d" % (lang['code'], lang['name'].lower(), langSum)
    print "\n"

########################################## format ##########################################
def partFormat(searchPath):

    if recursive: # scan directories recursively
        print "\nSearching %s recursively for files ending with %s" % (searchPath, suffix)
        if findCode:
            print "with language code %s" % findCode
        for root, dirs, files in os.walk(searchPath):
            for file in files:
                if isFile(os.path.join(root, file), suffix): # check if file matches criteria
                    print "\n%s" % os.path.join(root, file)
                    coding = checkCoding(os.path.join(root, file)) # get coding for file
                    if coding == prefEncoding:
                        print "--- Encoded in %s" % coding # correct encoding
                    else:
                        print "*** Encoded in %s" % coding # wrong encoding

    else: # scan single directory
        print "\nSearching %s for files ending with %s" % (searchPath, suffix)
        if findCode:
            print "with language code %s" % findCode
        for file in os.listdir(searchPath):
            if isFile(os.path.join(searchPath, file), suffix): # check if file matches criteria
                print "\n%s" % file
                coding = checkCoding(os.path.join(searchPath, file))
                if coding == prefEncoding:
                    print "--- Encoded in %s" % coding # correct encoding
                else:
                    print "*** Encoded in %s" % coding # wrong encodin

########################################## choose what to run ##########################################
if doLink and not doStatus and not doGet and not doCheck and not doFormat: # find language in subs and create links
    partLink(recursive, searchPath, suffix)

elif doStatus and not doLink and not doGet and not doCheck and not doFormat: # status
    partStatus()

elif doGet and not doLink and not doStatus and not doCheck and not doFormat: # get subs for video files
    partGet(searchPath)

elif doFormat and not doLink and not doGet and not doCheck and not doStatus: # check subs format, convert to UTF8 and convert to srt
    partFormat(searchPath)

elif doLink and doGet and not doStatus: # get and link
    partGet(searchPath)
    partLink(recursive, searchPath, suffix)

elif doCheck and not doLink and not doGet and not doStatus: # check
    partCheck(recursive, searchPath, suffix, findCode)

else:
    onError(5, 5)
