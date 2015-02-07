#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import os

from myFunctions import (findVideoFiles, hasSub, 
                         prefLangs, langName)

def partGet(searchPath, recursive, getSubs, fileMask, verbose):  # search for and download subtitles for your preferred languages
    videoFiles = []
    subDownloads = []
    
    videoFiles = findVideoFiles(searchPath, recursive, videoFiles, verbose)

    if videoFiles:
        for myFile in videoFiles:
            print "\n%s" % myFile
            if fileMask in os.path.basename(myFile):
                subDownloads = hasSub(myFile, searchPath, subDownloads, getSubs, verbose)  # go ahead processing the video file
            else:
                print "*** File name does not match the mask"

    if subDownloads:
        print "\nDownloaded subtitles:"
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

    print
