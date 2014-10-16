#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from myFunctions import *

def partGet(searchPath, recursive, verbose): # search for and download subtitles for your preferred languages
    videoFiles = []
    subDownloads = []
    
    videoFiles = findVideoFiles(searchPath, recursive, videoFiles, verbose)

    if videoFiles:
        for myFile in videoFiles:
            print "\n%s" % myFile
            subDownloads = hasSub(myFile, searchPath, subDownloads, verbose) # go ahead processing the video file

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