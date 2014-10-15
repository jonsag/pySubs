#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from myFunctions import *

def partCheck(recursive, searchPath, extension, findCode, verbose): # check if language code set is correct
    langSums = []
    num = 0

    if recursive: # scan directories recursively
        print "\nSearching %s recursively for files ending with %s" % (searchPath, extension)
        if findCode:
            print "with language code %s" % findCode
        for root, dirs, files in os.walk(searchPath):
            for myFile in files:
                if isFile(os.path.join(root, myFile), extension, verbose): # check if myFile matches criteria
                    print "\n%s" % myFile
                    existingCode = hasLangCode(os.path.join(searchPath, myFile))
                    if existingCode:
                        if findCode:
                            if existingCode['code'] == str(findCode):
                                print "\n%s" % os.path.join(root, myFile)
                                print "--- Has language code %s - %s" % (existingCode['code'], existingCode['name'].lower())
                                checkedCode = checkLang(os.path.join(root, myFile), 1) # let detectlanguage.com see what language the file has
                                compareCodes(existingCode['code'], checkedCode, os.path.join(str(root), myFile))
                                num += 1
                        else:
                            if existingCode:
                                print "\n%s" % os.path.join(root, myFile)
                                print "--- Has language code %s - %s" % (existingCode['code'], existingCode['name'].lower())
                                checkedCode = checkLang(os.path.join(root, myFile), 1) # let detectlanguage.com see what language the file has
                                compareCodes(existingCode['code'], checkedCode, os.path.join(str(root), myFile)) # compare existing and checked code
                                num += 1
                            else:
                                print "*** Has no language code"
  
    else: # scan single directory
        print "\nSearching %s for files ending with %s" % (searchPath, extension)
        if findCode:
            print "with language code %s" % findCode
        for myFile in os.listdir(searchPath):
            if isFile(os.path.join(searchPath, myFile), extension, verbose): # check if myFile matches criteria
                print "\n%s" % myFile
                existingCode = hasLangCode(os.path.join(searchPath, myFile))
                if existingCode:
                    print "--- Has language code %s - %s" % (existingCode['code'], existingCode['name'].lower())
                    checkedCode = checkLang(myFile, 1)  # let detectlanguage.com see what language the file has
                    compareCodes(existingCode['code'], checkedCode, myFile)
                    num += 1
                else:
                    print "*** Has no language code"

    print "\nNumber of %s files in %s: %d\n" % (extension, searchPath, num)

    print "Languages found:"
    for lang in languages:
        langSum = langSums.count(lang['code'])
        if langSums.count(lang['code']) > 0:
            print "%s - %s:  %d" % (lang['code'], lang['name'].lower(), langSum)
    print "\n"