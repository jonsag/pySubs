#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import os

from myFunctions import (findSubFiles, fileFound, 
                         languages)

def partLink(recursive, searchPath, extension, fileMask, verbose):  # finds out language of sub, inserts it, and creates link
    langSums = []
    subFiles = []

    subFiles = findSubFiles(searchPath, recursive, extension, subFiles, False, verbose)

    if subFiles: 
        for myFile in subFiles:
            print("\n%s" % myFile)
            if fileMask in os.path.basename(myFile):
                langSums = fileFound(myFile, langSums, verbose)  # go ahead with the file
            else:
                print("*** File name does not match the mask")

    print("\nLanguages found:")
    for lang in languages:
        langSum = langSums.count(lang['code'])  # adds languages found
        if langSums.count(lang['code']) > 0:  # if language found, print it
            print("%s - %s:  %d" % (lang['code'], lang['name'].lower(), langSum))
    print("\n")
