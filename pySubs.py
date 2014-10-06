#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

# edit .conf to suit your needs

import getopt

from myFunctions import * 

##### handle arguments #####
try:
    myopts, args = getopt.getopt(sys.argv[1:],'p:re:ldgc:fskhv' , ['path=', 'recursive', 'extension=', 'link', 'detectlang', 'get', 'check=', 'format', 'search', 'keep', 'help', 'verbose'])

except getopt.GetoptError as e:
    onError(1, str(e))

recursive = False
extension = ".srt"
searchPath = os.path.abspath(os.getcwd())
doLink = False
doStatus = False
doGet = False
doCheck = False
doFormat = False
verbose = False
keep = False
findCode = ""

if len(sys.argv) == 1: # no options passed
    onError(2, 2)

for option, argument in myopts:
    if option in ('-p', '--path'):
        searchPath = os.path.abspath(argument)
    elif option in ('-r', '--recursive'):
        recursive = True
    elif option in ('-e', '--extension'):
        extension = argument
    elif option in ('-l', '--link'):
        doLink = True
    elif option in ('-d', '--detectlang'):
        doStatus = True
    elif option in ('-g', '--get'):
        doGet = True
    elif option in ('-h', '--help'):
        usage(0)
    elif option in ('-c', '--check'):
        doCheck = True
        if argument == "all" or argument == "pref":
            findCode = argument
        else:
            for language in languages:
                if argument == language['code']:
                    findCode = argument
        if not findCode:
            onError(6, argument)
    elif option in ('-f', '--format'):
        doFormat = True
    elif option in ('-k', '--keep'):
        keep = True
    elif option in ('-v', '--verbose'):
        verbose = True

if not doLink and not doStatus and not doGet and not doCheck and not doFormat: # no program part selected
    onError(3, 3)

if searchPath: # argument -p --path passed
    if not os.path.isdir(searchPath): # not a valid path
        onError(4, searchPath)
else:
    print "\nNo path given."
    print "Using current dir %s" % searchPath

if extension: # argument -e --extension passed
    extension = ".%s" % extension.lstrip('.') # remove leading . if any
else:
    print "\nNo extension given!"
    print "Setting %s" % extension.lstrip('.') # remove leading . if any

########################################## link ##########################################
def partLink(recursive, searchPath, extension): # finds out language of sub, inserts it, and creates link
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

########################################## status ##########################################
def partStatus(): # check accounts status at detectlanguage.com
    print "\nAvailable languages:"
    print "-------------------------------------------------------------------------------------"
    for language in languages:
        print "%s %s" %(language['code'], language['name'])

    print "\n%d available languages" % len(languages)

    status = detectlanguage.user_status() # calls detectlanguage.com for account status

    print "\ndetectlanguage.com status for API-key: %s" % detectlanguage.configuration.api_key
    print "-------------------------------------------------------------------------------------"
    print "Status: %s" %status['status']
    print "Account type/plan: %s" % status['plan']
    print "\nTodays date: %s" % status['date']
    print "Plan expires: %s" % status['plan_expires']
    print '\nRequest: %d / %d' % (status['requests'], status['daily_requests_limit'])
    print 'Bytes: %d / %d' % (status['bytes'], status['daily_bytes_limit'])
    
########################################## get ##########################################
def partGet(searchPath): # search for and download subtitles for your preferred languages
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

########################################## check ##########################################
def partCheck(recursive, searchPath, extension, findCode): # check if language code set is correct
    langSums = []
    num = 0

    if recursive: # scan directories recursively
        print "\nSearching %s recursively for files ending with %s" % (searchPath, extension)
        if findCode:
            print "with language code %s" % findCode
        for root, dirs, files in os.walk(searchPath):
            for myFile in files:
                if isFile(os.path.join(root, myFile), extension, verbose): # check if myFile matches criteria
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

########################################## format ##########################################
def partFormat(searchPath): # check subtitles encoding and format
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
    

########################################## choose what to run ##########################################
if doLink and not doStatus and not doGet and not doCheck and not doFormat: # find language in subs and create links
    partLink(recursive, searchPath, extension)

elif doStatus and not doLink and not doGet and not doCheck and not doFormat: # status at detectlanguage.com
    partStatus()

elif doGet and not doLink and not doStatus and not doCheck and not doFormat: # get subs for video files
    partGet(searchPath)

elif doFormat and not doLink and not doGet and not doCheck and not doStatus: # check subs format, convert to UTF-8 and convert to srt
    partFormat(searchPath)

elif doLink and doGet and not doStatus and not doFormat: # get and link
    partGet(searchPath)
    print "----------------------------------------------------------------"
    partLink(recursive, searchPath, extension)

elif doFormat and doLink and not doGet and not doStatus and not doCheck: # format and link
    partFormat(searchPath)
    print "----------------------------------------------------------------"
    partLink(recursive, searchPath, extension)

elif doCheck and not doLink and not doGet and not doStatus and not doFormat: # check language codes manually
    partCheck(recursive, searchPath, extension, findCode)

else:
    onError(5, 5)
