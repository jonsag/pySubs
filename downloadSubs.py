#!/usr/bin/env python
# -*- coding: utf-8 -*-

# edit .conf to suit your needs

# options:
# -p <path> scan single path
# -r <path> scan path recursively
# -s <suffix> file suffix to search for

import sys, getopt, os

from myFunctions import *

##### set config file #####
#config = configparser.ConfigParser()
#config.sections()
#config.read('setSubLang.ini') # read config file

# create cache file
if not os.path.isfile(dbmCacheFile):
    print "Creating dbm cache file at %s" % dbmCacheFile

##### handle arguments #####
try:
    myopts, args = getopt.getopt(sys.argv[1:],"p:r:s:")
except getopt.GetoptError as e:
    print (str(e))
    print '\nUsage:'
    print '%s -p <path>>' % sys.argv[0]
    sys.exit(2)

for o, a in myopts:
    if o == '-p':
        searchPath = a

# check that a path is given
if not searchPath:
    print "\nError: No search path given!"
    print '\nUsage:'
    print '%s -p <path>' % sys.argv[0]
    sys.exit(3)

# check that path exists
if not os.path.isdir(searchPath):
    print "\nError: %s is not a valid path!" % searchPath
    sys.exit(6)

print "\nSearching %s for video files" % searchPath

# scan single directory
if searchPath:
    for file in os.listdir(searchPath):
        videoFound = False
        for suffix in videoSuffixes:
            if isVideo(file, suffix):
                print "\n%s" % file
                num += 1
                videoFound = True
                break
        if videoFound:
            #print "--- Checking if file already has subs"
            subDownloads = hasSub(file)
        #else:
        #    print "*** This is not a video file"
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
