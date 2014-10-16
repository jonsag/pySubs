#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from myFunctions import *

def partFormat(searchPath, recursive, extension, keep, verbose): # check subtitles encoding and format
    noFormat = 0
    srtFormat = 0
    samiFormat = 0
    dfxpFormat = 0
    wrongEncoding = 0
    wrongNumbering = 0
    #wrongFormat = 0
    emptyEntry = 0
    subFiles = []

    subFiles = findSubFiles(searchPath, recursive, extension, subFiles, False, verbose)
    
    if subFiles:
        for myFile in subFiles:
            print "\n%s" % myFile
            encoding = checkCoding(myFile, verbose) # check encoding
            if encoding == prefEncoding:
                print "--- Encoded in %s" % encoding # correct encoding
            else:
                print "*** Encoded in %s" % encoding # wrong encoding
                changeEncoding(myFile, encoding, keep, verbose) # set to preferred encoding
                wrongEncoding += 1

            myFormat = checkFormat(myFile, verbose) # check format
            if not myFormat:
                print "*** Could not detect format"
                noFormat += 1
            elif myFormat == "srt":
                print "--- Srt format"
                srtFormat += 1
                if emptyEntries(myFile, keep, verbose): # look for empty entries, if so delete them
                    emptyEntry += 1
                if numbering(myFile, keep, verbose): # check if numbering is correct, if not correct it
                    wrongNumbering += 1
            elif myFormat == "sami":
                print "*** Sami format"
                samiFormat += 1
                samiToSrt(myFile, keep, verbose) # convert from SAMI to SRT
                if emptyEntries(myFile, keep, verbose): # check for empty entries, if so delete them
                    emptyEntry += 1
                if numbering(myFile, keep, verbose): # check if numbering is correct, if not correct it
                    wrongNumbering += 1
            elif myFormat == "dfxp":
                print "*** Dfxp format"
                dfxpFormat += 1
                dfxpToSrt(myFile, keep, verbose) # convert from DFXP to SRT

    if noFormat + srtFormat + samiFormat > 0:
        print "\nFormats:"
        if noFormat > 0:
            print "Not detected: %s" % noFormat
        if srtFormat > 0:
            print "srt: %s" % srtFormat
        if samiFormat > 0:
            print "sami: %s" % samiFormat
        if dfxpFormat > 0:
            print "dfxp: %s" % dfxpFormat
        print

    if wrongEncoding > 0:
        print "Files with wrong encoding: %s" % wrongEncoding
        print

    if emptyEntry > 0:
        print "Files with empty entries: %s" % emptyEntry
        print

    if wrongNumbering > 0:
        print "File with wrong numbering: %s" % wrongNumbering
        print