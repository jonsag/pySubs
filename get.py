#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from myFunctions import *

def partGet(searchPath, recursive, verbose): # search for and download subtitles for your preferred languages
    subDownloads = []
    num = 0

    if recursive: # scan directories recursively
        print "\nSearching %s recursively for video files" % searchPath
        for root, dirs, files in os.walk(searchPath):
            for myFile in files:
                videoFound = False
                for extension in videoExtensions:
                    if isVideo(os.path.join(str(root), myFile), extension): # check if myFile matches any of the video extensions
                        print "\n%s" % os.path.join(str(root), myFile)
                        num += 1
                        videoFound = True
                        break
                if videoFound:
                    subDownloads = hasSub(os.path.join(str(root), myFile), searchPath) # go ahead processing the video file
    else:
        print "\nSearching %s for video files" % searchPath
        for myFile in os.listdir(searchPath):
            videoFound = False
            for extension in videoExtensions:
                if isVideo(myFile, extension): # check if myFile matches any of the video extensions
                    print "\n%s" % myFile
                    num += 1
                    videoFound = True
                    break
            if videoFound:
                subDownloads = hasSub(myFile, searchPath) # go ahead processing the video file

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