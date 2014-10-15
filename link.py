#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from myFunctions import *

def partLink(recursive, searchPath, extension, verbose): # finds out language of sub, inserts it, and creates link
    langSums = []
    num = 0

    if recursive: # scan directories recursively
        print "\nSearching %s recursively for files ending with %s" % (searchPath, extension)
        for root, dirs, files in os.walk(searchPath):
            for myFile in files:
                if isFile(os.path.join(root, myFile), extension, verbose): # check if myFile matches criteria
                    print "\n%s" % os.path.join(root, myFile)
                    langSums = fileFound(os.path.join(root, myFile), langSums, verbose) # go ahead with the file
                    num += 1

    else: # scan single directory
        print "\nSearching %s for files ending with %s" % (searchPath, extension)
        for myFile in os.listdir(searchPath):
            if isFile(os.path.join(searchPath, myFile), extension, verbose): # check if myFile matches criteria
                print "\n%s" % myFile
                langSums = fileFound(os.path.join(searchPath, myFile), langSums, verbose) # go ahead with the file
                num += 1

    print "\nNumber of %s files in %s: %d\n" % (extension, searchPath, num)

    print "Languages found:"
    for lang in languages:
        langSum = langSums.count(lang['code']) # adds languages found
        if langSums.count(lang['code']) > 0: # if language found, print it
            print "%s - %s:  %d" % (lang['code'], lang['name'].lower(), langSum)
    print "\n"