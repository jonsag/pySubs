#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from myFunctions import *

def partFormat(searchPath, recursive, extension, findCode, keep, verbose): # check subtitles encoding and format
    noFormat = 0
    srtFormat = 0
    samiFormat = 0
    dfxpFormat = 0
    wrongEncoding = 0
    wrongNumbering = 0
    #wrongFormat = 0
    emptyEntry = 0

    if recursive: # scan directories recursively
        print "\nSearching %s recursively for files ending with %s" % (searchPath, extension)
        if findCode:
            print "with language code %s" % findCode
        for root, dirs, files in os.walk(searchPath):
            for myFile in files:
                if isFile(os.path.join(root, myFile), extension, verbose): # check if myFile matches criteria
                    print "\n%s" % os.path.join(root, myFile)

                    encoding = checkCoding(os.path.join(root, myFile), verbose) # check encoding
                    if encoding == prefEncoding:
                        print "--- Encoded in %s" % encoding # correct encoding
                    else:
                        print "*** Encoded in %s" % encoding # wrong encoding
                        changeEncoding(os.path.join(root, myFile), encoding, keep, verbose) # set to preferred encoding
                        wrongEncoding += 1

                    myFormat = checkFormat(os.path.join(root, myFile), verbose) # check format
                    if not myFormat:
                        print "*** Could not detect format"
                        noFormat += 1
                    elif myFormat == "srt":
                        print "--- Srt format"
                        srtFormat += 1
                        if emptyEntries(os.path.join(root, myFile), keep, verbose): # look for empty entries, if so delete them
                            emptyEntry += 1
                        if numbering(os.path.join(root, myFile), keep, verbose): # check if numbering is correct, if not correct it
                            wrongNumbering += 1
                    elif myFormat == "sami":
                        print "*** Sami format"
                        samiFormat += 1
                        samiToSrt(os.path.join(root, myFile), keep, verbose) # convert from SAMI to SRT
                        if emptyEntries(os.path.join(root, myFile), keep, verbose): # check for empty entries, if so delete them
                            emptyEntry += 1
                        if numbering(os.path.join(root, myFile), keep, verbose): # check if numbering is correct, if not correct it
                            wrongNumbering += 1
                    elif myFormat == "dfxp":
                        print "*** Dfxp format"
                        dfxpFormat += 1
                        dfxpToSrt(os.path.join(root, myFile), keep, verbose) # convert from DFXP to SRT

    else: # scan single directory
        print "\nSearching %s for files ending with %s" % (searchPath, extension)
        if findCode:
            print "with language code %s" % findCode
        for myFile in os.listdir(searchPath):
            if isFile(os.path.join(searchPath, myFile), extension, verbose): # check if myFile matches criteria
                print "\n%s" % myFile

                encoding = checkCoding(os.path.join(searchPath, myFile), verbose) # check encoding
                if encoding == prefEncoding:
                    print "--- Encoded in %s" % encoding # correct encoding
                else:
                    print "*** Encoded in %s" % encoding # wrong encoding
                    changeEncoding(os.path.join(searchPath, myFile), encoding, keep, verbose) # set to preferred encoding
                    wrongEncoding += 1
                    
                myFormat = checkFormat(os.path.join(searchPath, myFile), verbose) # check format
                if not myFormat:
                    print "*** Could not detect format"
                    noFormat += 1
                elif myFormat == "srt":
                    print "--- Srt format"
                    srtFormat += 1
                    if emptyEntries(os.path.join(searchPath, myFile), keep, verbose): # look for empty entries, if so delete them
                        emptyEntry += 1
                    if numbering(os.path.join(searchPath, myFile), keep, verbose): # check if numbering is correct, if not correct it
                        wrongNumbering += 1
                elif myFormat == "sami":
                    print "*** Sami format"
                    samiFormat += 1
                    samiToSrt(os.path.join(searchPath, myFile), keep, verbose) # convert from SAMI to SRT
                    if emptyEntries(os.path.join(searchPath, myFile), keep, verbose): # look for empty entries, if so delete them
                        emptyEntry += 1
                    if numbering(os.path.join(searchPath, myFile), keep, verbose): # check if numbering is correct, if not correct it
                        wrongNumbering += 1
                elif myFormat == "dfxp":
                    print "*** Dfxp format"
                    dfxpFormat += 1
                    dfxpToSrt(os.path.join(searchPath, myFile), keep, verbose) # convert from DFXP to SRT

    print "\nNumber of %s files in %s: %d\n" % (extension, searchPath, noFormat + srtFormat + samiFormat)

    if noFormat + srtFormat + samiFormat > 0:
        print "Formats:"
        if noFormat > 0:
            print "Not detected: %s" % noFormat
        if srtFormat > 0:
            print "srt: %s" % srtFormat
        if samiFormat > 0:
            print "sami: %s" % samiFormat
        if dfxpFormat > 0:
            print "dfxp: %s" % dfxpFormat
        print "\n"

    if wrongEncoding > 0:
        print "Files with wrong encoding: %s" % wrongEncoding
        print "\n"

    if emptyEntry > 0:
        print "Files with empty entries: %s" % emptyEntry
        print "\n"

    if wrongNumbering > 0:
        print "File with wrong numbering: %s" % wrongNumbering
        print "\n"