#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import re, sys, ConfigParser, os, detectlanguage, codecs

from itertools import islice
from sys import exit
from string import digits
from collections import namedtuple
from subprocess import call

# libraries for subliminal
#from __future__ import unicode_literals  # python 2 only
from babelfish import Language
from datetime import timedelta
import subliminal

# starting up some variables
num = 0
searchPath = ""
searchPathRecursive = ""
suffix = ""
langSums = []
subDownloads = []

config = ConfigParser.ConfigParser()
config.read("%s/config.ini" % os.path.dirname(__file__)) # read config file

##### mainly for subGetLangs #####
prefLangs = (config.get('languages','prefLangs')).split(',') # prefered languages

detectRows = int(config.get('variables','detectRows')) # number of rows sent to detectlanguage.com in each trys
detectTrys = int(config.get('variables','detectTrys')) # number of trys to detect language at detectlanguage.com

detectlanguage.configuration.api_key = config.get('detectlanguage_com','api-key') # api-key to detectlanguage.com from config file

languages = detectlanguage.languages() # get available languages from detectlanguage.com

languages.append({u'code': u'xx', u'name': u'UNKNOWN'})

def usage(exitCode):
    print "\nUsage:"
    print "----------------------------------------"
    print "%s -l [-p <path>] [-r] [-s <suffix>]" % sys.argv[0]
    print "          Find files, set language code if none, and create symbolic 'l'ink to them without language code"
    print "          Options: Set -s <suffix> to set suffix to search for"
    print "              Set -r to search 'r'ecursively"
    print "              Set -p <path> to set other path than current"
    print "     OR"
    print "%s -d" % sys.argv[0]
    print "          Get available languages from 'd'etectlanguage.com, and your account status at the same place"
    print "     OR"
    print "%s -g [-p <path>] [-r] [-s <suffix>]" % sys.argv[0]
    print "          Search video files, check if there are any srt subtitle files with language code in the name"
    print "          If not try to find and 'g'et subtitles in any of your preferred languages"
    print "          Options: Set -r to search 'r'ecursively"
    print "                   Set -p <path> to set other path than current"
    print "     OR"
    print "%s -h" % sys.argv[0]
    print "          Prints this"
    print "\n"
    sys.exit(exitCode)

##### mainly for downloadSubs #####
dbmCacheFile = "%s/%s/cachefile.dbm" % (os.path.expanduser("~"), config.get('video','dbmCacheFile')) # get location for dbm cache file

videoSuffixes = (config.get('video','videoSuffixes')).split(',') # load video suffixes

def isFile(file, suffix): # returns True if suffix is correct, is a file, is not a link and is not empty
    result = False # set default result False
    fileExtension = os.path.splitext(file)[1] # get extension only with the leading punctuation
    if fileExtension.lower() == suffix and os.path.isfile(file) and not os.path.islink(file): # file ends with correct suffix, is a file and is not a link
        print "\n%s" % file
        if fileEmpty(file): # file is empty
            print "*** File is empty. Deleting it..."
            os.remove(file)
        else:
            result = True # file ends with correct suffix, is a file, is not a link and is empty
    return result

def hasLangCode(file): # returns the language code present, if there is one. Otherwise returns "none"
    result = "none" # default return code
    fileName = os.path.splitext(file)[0] # file name without punctuation and suffix
    for code in languages:
        if '.%s' % code['code'] == os.path.splitext(fileName)[1] or '.%s' % "xx" == os.path.splitext(fileName)[1]: # adds punctuation before code, and compares to suffix in stripped file name. If same, returns code
            result = code # set detected language code to result
    return result # return detected language code

def fileFound(file, langSums): # runs on every file that matches suffix, is not a link and is not empty
    acceptUnreliable = config.get('variables','acceptUnreliable') # True if we accept unreliable as language code
    codePresent = hasLangCode(file) # check if the file already has a language code. Returns code if there is one, otherwise "none"

    if codePresent == "none": # file name has no language code
        checkCode = checkLang(file) # determine what language file has. Returns language code
        if acceptUnreliable: # we accept "unreliable" as language code
            addLangCode(file, checkCode) # add language code to file name
            langSums = foundLang(checkCode) # sending language code to be added if code was not present and we accept "xx" as language code
        else: # we don't accept "xx" as language code
            if checkCode != "xx": # if the language code is reliable
                addLangCode(file, checkCode) # add language code to file name
            else:
                print "*** Can't determine if language code present is correct. Doing nothing further"

    else: # file name has language code
        print "*** Already has language code %s - %s" % (codePresent['code'], codePresent['name'])
        langSums = foundLang(codePresent['code']) # sending language code to be added if language code was present

        if hasLink(file) and codePresent != "xx": # file has link and language code is not xx
            print "*** Already has link"
            if codePresent['code'] == prefLangs[0]: # language code for this file is your first prefered one
                print "--- Language code for this file is %s. Creating new link anyway" % prefLangs[0]
                makeLink(file) # create a link to the file

        elif codePresent == "xx": # language code is "xx"
            checkCode = checkLang(file) # determine what language file has at detectlanguage.com. Returns language code

            if acceptUnreliable: # we accept "xx" as language code
                if checkCode == codePresent['code']: # correct language code already set
                    print "--- Present language code seems correct!"
                    makeLink(file) # create a link to the file
                else: # wrong code set to file
                    print "*** Present language code don't seem correct. Changing %s to %s" % (codePresent['code'], checkCode) 
                    file = changeCode(file, checkCode) # set correct language code to file, and get the new file name
                    makeLink(file) # create a link to the file
            else: # we don't accept "xx" as language code
                if checkCode == "xx": # language result is unknown
                    print "*** Can't determine if language code present is correct. Doing nothing further"
                else: # if the the result is reliable
                    if checkCode == codePresent: # correct language code already set
                        print "--- Present language code seems correct!"
                    else: # wrong code set to file
                        print "*** Present language code don't seem correct. Changing %s to %s" % (codePresent['code'], checkCode)
                        file = changeCode(file, checkCode) # set correct language code to file, and get the new file name
                        makeLink(file) # create a link to the file, if it already has correct language code

        else:
            makeLink(file) # create a link to the file
            #langSums = foundLang(codePresent['code']) # sending language code to be added
    return langSums

def makeLink(file): # create a link to file that has language code
    print "--- Creating link for %s" % file
    linkName = "%s%s" % (os.path.splitext(os.path.splitext(file)[0])[0], os.path.splitext(file)[1]) # remove suffix, remove another suffix and add first suffix again
    if os.path.isfile(linkName) and not os.path.islink(linkName): # the new link would overwrite a file
        print "*** %s is a file. Skipping" % linkName
    else:
        if os.path.islink(linkName): # the new link would overwrite an old link
            print "*** %s exists as a link. Removing it..." % linkName
            os.unlink(linkName) # delete old link
        print "--- Creating link %s" % linkName
        os.symlink(os.path.basename(file), linkName) # create a link pointing to the file with link name without language code
    return

def addLangCode(file, langCode): # adds language code to file name
    print "--- Adding language code to %s" % file
    # takes filename without suffix, adds punctuation and language code and adds the old suffix
    newName = "%s.%s%s" % (os.path.splitext(file)[0], langCode, os.path.splitext(file)[1])
    if os.path.isfile(newName): # new file name exists as a file
        print "*** %s already exist. Skipping..." % newName
    else:
        print "--- Renaming to %s" % newName
        os.rename(file, newName) # rename the file
        makeLink(newName) # make link to file

def checkLang(file): # checks file for language and returns language code, or if is doubtful returns "xx"
    status = detectlanguage.user_status() # get status for the account at detectlanguage.com
    tryNumber = 0 # starting up counter
    finished = False
    if status['status'] == "SUSPENDED":
        print "*** Account at detectlanguage.com is suspended"
        print "    Run %s -d to see status" % sys.argv[0]
        print "    Quitting...\n"
        exit(7)
    with codecs.open(file, encoding='utf8') as myfile:
        fileLines = sum(1 for line in myfile) # number of lines in file
    myfile.close() # close file
    while True:
        if tryNumber * detectRows >= fileLines:
            print "*** File only has %d lines. No more lines to send. Accepting answer" % fileLines
            break

        with open(file) as myFile: # open file
            head = list(islice(myFile, tryNumber * detectRows, (tryNumber + 1) * detectRows)) # select rows from file
        myFile.close() # close file

        text = convertText(head) # convert all strange characters, remove special characters and so on

        print "--- Sending rows %d-%d to detectlanguage.com" % (tryNumber * detectRows, (tryNumber + 1) * detectRows)
        result = detectlanguage.detect(text) # detect language

        if result[0]['isReliable']: # result is reliable
            langCode = str(result[0]['language']) # langCode set to answer from detectlanguage.com
            print "--- Got %s - %s" % (langCode, langName(langCode))

            for lang in prefLangs: # run through the prefered languages
                if lang == langCode: # recieved language is one of the prefered languages
                    finished = True # search for language code is finished
                    break # break out of this for loop
                else:
                    print "*** Not one of the prefered languages"

            if finished:
                break # break out of the while loop

        else:
            langCode = "xx"
            print "*** Got unreliable answer. Confidence is %s" % str(result[0]['confidence'])
        tryNumber += 1 # counting number of trys
        if tryNumber > detectTrys: # reached maximum number of trys
            print "*** Max number of trys reached. Accepting answer"
            finished = True
            #break
        if finished:
            break

    if langCode == "xx":
        print "detectlanguage.com can't determine language code"
    else:
        print "detectlanguage.com says languagecode is %s" % langCode

    confidence = result[0]['confidence']
    print "detectlanguage.com says confidence is %s" % confidence
    return langCode

def changeCode(file, newCode): # change language code to newCode
    newName = "%s.%s%s" % (os.path.splitext(os.path.splitext(file)[0])[0], newCode, os.path.splitext(file)[1]) # file name without punctuation and last two suffixes
    print "--- Renaming to %s" % newName
    os.rename(file, newName) # rename the file
    return newName

def hasLink(file): # return True if the file already has a link to it, excluding the language code
    result = False
    linkName = "%s%s" % (os.path.splitext(os.path.splitext(file)[0])[0], os.path.splitext(file)[1])
    if os.path.islink(linkName): # there is a link to the file
        result = True
    return result

def fileEmpty(file): # returns True is file is empty
    #import os
    return os.stat(file).st_size==0

def langName(langCode): # returns language name from language code
    for lang in languages:
        if langCode == lang['code']:
            result = lang['name']
            break
    return result

def foundLang(langCode): # add language code to langSums
    langSums.append(langCode)    
    return langSums

def convertText(head):
        text1 = str(head) # make string of array
        text2 = text1.split("\\r\\n', '")
        text3 = []
        text4 = []
        text = ""
        for line in text2:
            if line != "\\r\\n']" and line != "['1" and not re.match("^[0-9:\-.> ]*$", line):
                    text3.append(line)
        for line in text3:
            text4.append(line.replace('\\xc3\\xa5','å').replace('\\xc3\\xa4','ä').replace('\\xc3\\xb6','ö').replace('\\xc3\\x85', 'Å').replace('\\xc3\\x84', 'Ä').replace('\\xc3\\x96', 'Ö').rstrip('\-').lstrip('\-'))
        for line in text4:
            text = "%s %s" % (text, line)
        return text

def isVideo(file, suffix):
    result = False
    fileExtension = os.path.splitext(file)[1]
    if fileExtension.lower() == ".%s" % suffix:
        result = True
    return result

def hasSub(file):
    subName = os.path.splitext(file)[0]
    for lang in prefLangs:
        subNameLang = "%s.%s.%s" % (subName, lang, "srt")
        if os.path.isfile(subNameLang):
            print "--- Already has %s subtitles" % langName(lang).lower()
            subDownloads = foundLang("%s - present" % lang)
        else:
            print "*** Has no %s subtitles" % langName(lang).lower()
            subDownloads = downloadSub(file, lang)
    return subDownloads

def downloadSub(file, lang):
    print "--- Trying to download..."
    
    if call(["subliminal", "-q", "-l", lang, "--", file]):
        print "*** Could not find %s subtitles" % langName(lang).lower()
        subDownloads = foundLang("%s - not found" % lang)
    else:
        print "--- Downloaded %s subtitles" % langName(lang).lower()
        subDownloads = foundLang(lang) # sending language code to be added
    return subDownloads
