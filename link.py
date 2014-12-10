#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from myFunctions import *

def partLink(recursive, searchPath, extension, verbose):  # finds out language of sub, inserts it, and creates link
    langSums = []
    subFiles = []

    subFiles = findSubFiles(searchPath, recursive, extension, subFiles, False, verbose)

    if subFiles: 
        for myFile in subFiles:
            print "\n%s" % myFile
            langSums = fileFound(myFile, langSums, verbose)  # go ahead with the file

    print "\nLanguages found:"
    for lang in languages:
        langSum = langSums.count(lang['code'])  # adds languages found
        if langSums.count(lang['code']) > 0:  # if language found, print it
            print "%s - %s:  %d" % (lang['code'], lang['name'].lower(), langSum)
    print "\n"
