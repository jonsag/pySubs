#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import sys, re, ConfigParser, os, detectlanguage, shlex

from itertools import islice
from sys import exit

from subprocess import call, Popen, PIPE

# libraries for subliminal
# from __future__ import unicode_literals  # python 2 only
from babelfish import Language
# from datetime import timedelta
# import subliminal
from subliminal import (download_best_subtitles, region, save_subtitles, Video, 
                        list_subtitles, compute_score)

# starting up some variables
# num = 0
searchPath = ""
searchPathRecursive = ""
extension = ""
langSums = []

config = ConfigParser.ConfigParser()
config.read("%s/config.ini" % os.path.dirname(__file__))  # read config file

##### mainly for subGetLangs #####
prefLangs = (config.get('languages', 'prefLangs').replace(" ", "")).split(',')  # prefered languages

detectRows = int(config.get('variables', 'detectRows'))  # number of rows sent to detectlanguage.com in each trys
maxTrys = int(config.get('variables', 'maxTrys'))  # number of trys to detect language at detectlanguage.com

detectlanguage.configuration.api_key = config.get('detectlanguage_com', 'api-key')  # api-key to detectlanguage.com from config file

theTVdbApiKey = config.get('thetvdb', 'theTVdbApiKey')

getMirrorXml = config.get('thetvdb', 'getMirrorXml')
getTimeXML = config.get('thetvdb', 'getTimeXml')
getSeriesXml = config.get('thetvdb', 'getSeriesXml')

timeOut = int(config.get('thetvdb', 'timeOut'))

def setupLanguages():
    trys = 0
    
    print "--- Getting languages..."
    while True:
        trys += 1
        if trys > maxTrys:
            onError(8, "Tried connecting %s times\nGiving up..." % trys)
        try:
            languages = detectlanguage.languages()  # get available languages from detectlanguage.com
        except:
            print "*** Could not connect to detectlanguage.com\n    Trying again"
        else:
            languages.append({u'code': u'xx', u'name': u'UNKNOWN'})
            break
    
    return languages

languages = setupLanguages()

translateEngines = (config.get('variables', 'translateEngines').replace(" ", "")).split(',')

# yandexGetLangsXML = config.get('yandex_com','yandexGetLangsXML')
# yandexGetLangsJSON = config.get('yandex_com','yandexGetLangsJSON')
# yandexDetectXML = config.get('yandex_com','yandexDetectXML')
# yandexDetectJSON = config.get('yandex_com','yandexDetectJSON')
yandexTranslateXML = config.get('yandex_com', 'yandexTranslateXML')
# yandexTranslateJSON = config.get('yandex_com','yandexTranslateJSON')

msAddress = config.get('microsoft_com', 'msAddress')
msClientID = config.get('microsoft_com', 'msClientID')
msClientSecret = config.get('microsoft_com', 'msClientSecret') 

prefEncoding = config.get('coding', 'prefEncoding')  # your preferred file encoding

debug = int(config.get('misc', 'debug'))

def onError(errorCode, extra):
    print "\nError: %s" % errorCode
    if errorCode in (1, 2, 3, 5, 6, 7, 9):
        print extra
        usage(errorCode)
    elif errorCode in (4, 8):
        print "%s\n" % extra
        sys.exit(errorCode)
    else:
        print "\nError: Unknown"

def usage(exitCode):
    print "\nUsage:"
    print "----------------------------------------"
    print "%s -l [-p <path>] [-r] [-m <mask>] [-e <extension>]" % sys.argv[0]
    print "          Find files, set language code if none, and create symbolic 'l'ink to them without language code"
    print "          Options: Set -e <extension> to set 's'uffix to search for"
    print "                   Set -r to search 'r'ecursively"
    print "                   Set -p <path> to set other 'p'ath than current"
    print "                   Set -m <mask> to only include files matching your mask"
    print
    print "%s -d" % sys.argv[0]
    print "          Get available languages from 'd'etectlanguage.com, and your account status at the same place"
    print
    print "%s -g all|pref|<lang> [-p <path>] [-r] [-m <mask>] [-e <extension>]" % sys.argv[0]
    print "          Search video files, check if there are any srt subtitle files with language code in the name"
    print "          If not try to find and 'g'et subtitles in any of your preferred languages"
    print "          Options: Set -r to search 'r'ecursively"
    print "                   Set -p <path> to set other 'p'ath than current"
    print "                   Set -m <mask> to only include files matching your mask"
    print
    print "%s -c all|pref|<code>|force [-p <path>] [-r]" % sys.argv[0]
    print "          'C'heck language codes set in filenames manually"
    print "          Arguments: all checks all files with languagecode set"
    print "                     pref checks all files with any of your preferred languages"
    print "                     <code>, give a valid language code"
    print "                     force checks all, and lets you decide"
    print "          Options: Set -e <extension> to set 's'uffix to search for"
    print "                   Set -r to search 'r'ecursively"
    print "                   Set -p <path> to set other 'p'ath than current"
    print
    print "%s -f [-k] [-p <path>] [-r] [-e <extension>]" % sys.argv[0]
    print "          Find subtitles, check 'f'ormat, and convert to UTF8, and convert to srt"
    print "          Options: Set -k to 'k'eep temporary file"
    print "                   Set -e <extension> to set 's'uffix to search for"
    print "                   Set -r to search 'r'ecursively"
    print "                   Set -p <path> to set other 'p'ath than current"
    print
    print "%s -h" % sys.argv[0]
    print "          Prints this"
    print "\n"
    sys.exit(exitCode)

##### mainly for downloadSubs #####
dbmCacheFile = "%s/%s/cachefile.dbm" % (os.path.expanduser("~"), config.get('video', 'dbmCacheFile'))  # get location for dbm cache file

videoExtensions = (config.get('video', 'videoExtensions').replace(" ", "")).split(',')  # load video extensions

def isSub(myFile, extension, verbose):  # returns True if extension is correct, is a file, is not a link and is not empty
    result = False  # set default result False
    # if verbose:
    #    print "--- Checking if %s matches our criteria" % myFile
    fileExtension = os.path.splitext(myFile)[1]  # get extension only with the leading punctuation
    if fileExtension.lower() == extension and os.path.isfile(myFile) and not os.path.islink(myFile):  # file ends with correct extension, is a file and is not a link
        if fileEmpty(myFile):  # myFile is empty
            print "\n%s" % myFile
            print "*** File is empty. Deleting it..."
            os.remove(myFile)
        else:
            result = True  # myFile ends with correct extension, is a file, is not a link and is empty
    return result

def hasLangCode(myFile):  # returns the language code present, if there is one. Otherwise returns empty
    result = ""  # default return code
    fileName = os.path.splitext(myFile)[0]  # myFile name without punctuation and extension
    for language in languages:
        if '.%s' % language['code'] == os.path.splitext(fileName)[1]:  # adds punctuation before code, and compares to extension in stripped file name. If same, returns code
            result = language  # set detected language code to result
    return result  # return detected language code

def fileFound(myFile, langSums, verbose):  # runs on every file that matches extension, is not a link and is not empty
    acceptUnreliable = config.get('variables', 'acceptUnreliable')  # True if we accept unreliable as language code
    codePresent = hasLangCode(myFile)  # check if the file already has a language code. Returns code if there is one, otherwise empty

    if not codePresent:  # file name has no language code
        checkCode = checkLang(myFile, verbose)  # determine what language file has. Returns language code
        if acceptUnreliable:  # we accept "unreliable" as language code
            addLangCode(myFile, checkCode)  # add language code to file name
            langSums = foundLang(checkCode)  # sending language code to be added if code was not present and we accept "xx" as language code
        else:  # we don't accept "xx" as language code
            if checkCode != "xx":  # if the language code is reliable
                addLangCode(myFile, checkCode)  # add language code to file name
            else:
                print "*** Can't determine if language code present is correct. Doing nothing further"

    else:  # file name has language code
        print "*** Already has language code %s - %s" % (codePresent['code'], codePresent['name'].lower())
        langSums = foundLang(codePresent['code'])  # sending language code to be added if language code was present

        if hasLink(myFile) and codePresent != "xx":  # file has link and language code is not xx
            print "*** Already has link"
            if codePresent['code'] == prefLangs[0]:  # language code for this file is your first prefered one
                print "--- Language code for this file is %s. Creating new link anyway" % prefLangs[0]
                makeLink(myFile)  # create a link to the file

        elif codePresent == "xx":  # language code is "xx"
            checkCode = checkLang(myFile, verbose)  # determine what language file has at detectlanguage.com. Returns language code

            if acceptUnreliable:  # we accept "xx" as language code
                if checkCode == codePresent['code']:  # correct language code already set
                    print "--- Present language code seems correct!"
                    makeLink(myFile)  # create a link to the file
                else:  # wrong code set to file
                    print "*** Present language code don't seem correct. Changing %s to %s" % (codePresent['code'], checkCode) 
                    myFile = changeCode(myFile, checkCode)  # set correct language code to myFile, and get the new file name
                    makeLink(myFile)  # create a link to the file
            else:  # we don't accept "xx" as language code
                if checkCode == "xx":  # language result is unknown
                    print "*** Can't determine if language code present is correct. Doing nothing further"
                else:  # if the the result is reliable
                    if checkCode == codePresent:  # correct language code already set
                        print "--- Present language code seems correct!"
                    else:  # wrong code set to file
                        print "*** Present language code don't seem correct. Changing %s to %s" % (codePresent['code'], checkCode)
                        myFile = changeCode(myFile, checkCode)  # set correct language code to myFile, and get the new file name
                        makeLink(myFile)  # create a link to the file, if it already has correct language code

        else:
            makeLink(myFile)  # create a link to the file
            # langSums = foundLang(codePresent['code']) # sending language code to be added
    return langSums

def makeLink(myFile):  # create a link to file that has language code
    print "--- Creating link"
    linkName = "%s%s" % (os.path.splitext(os.path.splitext(myFile)[0])[0], os.path.splitext(myFile)[1])  # remove extension, remove another extension and add first extension again
    if os.path.isfile(linkName) and not os.path.islink(linkName):  # the new link would overwrite a file
        print "*** %s is a file. Skipping" % linkName
    else:
        if os.path.islink(linkName):  # the new link would overwrite an old link
            print "*** %s exists as a link. Removing it..." % linkName
            os.unlink(linkName)  # delete old link
        print "--- Creating new link"
        os.symlink(os.path.basename(myFile), linkName)  # create a link pointing to the file with link name without language code
    return

def addLangCode(myFile, langCode):  # adds language code to file name
    print "--- Adding language code to %s" % myFile
    # takes filename without extension, adds punctuation and language code and adds the old extension
    newName = "%s.%s%s" % (os.path.splitext(myFile)[0], langCode, os.path.splitext(myFile)[1])
    if os.path.isfile(newName):  # new file name exists as a file
        print "*** %s already exist. Skipping..." % newName
    else:
        print "--- Renaming to %s" % newName
        os.rename(myFile, newName)  # rename the file
        makeLink(newName)  # make link to file

def checkLang(myFile, verbose):  # checks file for language and returns language code, or if is doubtful returns "xx"
    tryNumber = 0  # starting up counter
    finished = False
    status = detectlanguage.user_status()  # get status for the account at detectlanguage.com
    if status['status'] == "SUSPENDED":
        print "*** Account at detectlanguage.com is suspended"
        print "    Run %s -d to see status" % sys.argv[0]
        print "    Quitting...\n"
        exit(7)
    with open(myFile) as theFile:
        fileLines = sum(1 for line in theFile)  # number of lines in file
    theFile.close()  # close file
    while True:
        if tryNumber * detectRows >= fileLines:
            print "*** File only has %d lines. No more lines to send. Accepting answer" % fileLines
            break

        with open(myFile) as theFile:  # open file
            head = list(islice(theFile, tryNumber * detectRows, (tryNumber + 1) * detectRows))  # select rows from file
        theFile.close()  # close file

        text = convertText(head, verbose)  # convert all strange characters, remove special characters and so on

        print "--- Sending rows %d-%d to detectlanguage.com" % (tryNumber * detectRows, (tryNumber + 1) * detectRows)
        result = detectlanguage.detect(text)  # detect language

        if result[0]['isReliable']:  # result is reliable
            langCode = str(result[0]['language'])  # langCode set to answer from detectlanguage.com
            print "--- Got %s - %s" % (langCode, langName(langCode))

            for lang in prefLangs:  # run through the prefered languages
                if lang == langCode:  # recieved language is one of the prefered languages
                    finished = True  # search for language code is finished
                    break  # break out of this for loop

            if finished:
                break  # break out of the while loop
            else:
                print "*** Not one of your prefered languages"
        else:
            langCode = "xx"
            print "*** Got unreliable answer. Confidence is %s" % str(result[0]['confidence'])
        tryNumber += 1  # counting number of trys
        if tryNumber > maxTrys:  # reached maximum number of trys
            print "*** Max number of trys reached. Accepting answer"
            finished = True
            # break
        if finished:
            break

    if langCode == "xx":
        print "detectlanguage.com can't determine language code"
    else:
        print "detectlanguage.com says languagecode is %s" % langCode

    confidence = result[0]['confidence']
    print "detectlanguage.com says confidence is %s" % confidence
    return langCode

def changeCode(myFile, newCode):  # change language code to newCode
    newName = "%s.%s%s" % (os.path.splitext(os.path.splitext(myFile)[0])[0], newCode, os.path.splitext(myFile)[1])  # file name without punctuation and last two extensions
    print "--- Renaming to %s" % newName
    os.rename(myFile, newName)  # rename the file
    return newName

def hasLink(myFile):  # return True if the file already has a link to it, excluding the language code
    result = False
    linkName = "%s%s" % (os.path.splitext(os.path.splitext(myFile)[0])[0], os.path.splitext(myFile)[1])
    if os.path.islink(linkName):  # there is a link to the file
        result = True
    return result

def fileEmpty(myFile):  # returns True is file is empty
    return os.stat(myFile).st_size == 0

def langName(langCode):  # returns language name from language code
    result = ""
    for lang in languages:
        if langCode == lang['code']:
            result = lang['name']
            break
    return result

def foundLang(langCode):  # add language code to langSums
    langSums.append(langCode)    
    return langSums

def convertText(head, verbose):
        text = ""
        textc = []
        textd = []
        texte = []
        
        if debug:
            print "\nhead:"
            print "-" * 40
            print head
            print "-" * 40
            
        texta = str(head)  # make string of array
        if debug:
            print "\nstring:"
            print "-" * 40
            print texta
            print "-" * 40
            
        textb = texta.split("\\n")  # split string into list
        if debug:
            print "\nsplit:"
            print "-" * 40
            for line in textb:
                print line
            print "-" * 40
            
        for line in textb:
            texte.append(line.
                         rstrip("\\r"))
        
        for line in texte:  # process line by line, deleting all unwanted ones
            if (
                not line == "\\r\\n']" 
                and not line == "['1" 
                and not line == '"]' 
                and not line == "['1\\r" 
                and not line == "', '\\r"
                and not re.match("^[0-9:',.>'\- \]]*$", line)):
                textc.append(line)

        if debug:
            print "\nremoved lines:"
            print "-" * 40
            for line in textc:
                print line
            print "-" * 40

        for line in textc:  # append to text, converting all odd things...
            textd.append(line.
                         replace('\\xc3\\xa5', 'å').
                         replace('\\xc3\\xa4', 'ä').
                         replace('\\xc3\\xb6', 'ö').
                         replace('\\xc3\\x85', 'Å').
                         replace('\\xc3\\x84', 'Ä').
                         replace('\\xc3\\x96', 'Ö').
                         rstrip('\-').lstrip('\-').
                         lstrip("', '").lstrip("- ").
                         lstrip('"- ').lstrip(", '").
                         lstrip('"- ').rstrip("\\n']").
                         rstrip(" ").rstrip("\\r")
                         )

        if debug:
            print "\ncleaned:"
            print "-" * 40
            for line in textd:
                print line
            print "-" * 40

        for line in textd:
            text = "%s %s" % (text, line)
            
        text = text.replace("- ", " ")

        if verbose:
            print "\nText to examine:"
            print "-" * 40
            print text
            print "-" * 40
            print
        print
        
        return text

def isVideo(myFile, extension):
    result = False
    fileExtension = os.path.splitext(myFile)[1]
    if fileExtension.lower() == ".%s" % extension:
        result = True
    return result

def hasSub(myFile, path, subDownloads, getSubs, verbose):
    subName = os.path.splitext(myFile)[0]
    origWD = os.getcwd()  # current working directory
    os.chdir(path)  # change working directory to where the videos are
    
    if getSubs == "pref":
        print "--- Getting subs in your preferred languages..."
        for lang in prefLangs:
            subNameLang = "%s.%s.%s" % (subName, lang, "srt")
            if os.path.isfile(subNameLang):
                print "--- Already has %s subtitles" % langName(lang).lower()
                subDownloads = foundLang("%s - present" % lang)
            else:
                print "*** Has no %s subtitles" % langName(lang).lower()
                subDownloads = downloadSub(myFile, lang, path, verbose)
    elif getSubs == "all":
        print "--- Getting subs in all languages..."
        for lang in languages:
            subNameLang = "%s.%s.%s" % (subName, lang['code'], "srt")
            if os.path.isfile(subNameLang):
                print "--- Already has %s subtitles" % langName(lang['code']).lower()
                subDownloads = foundLang("%s - present" % lang['code'])
            else:
                print "*** Has no %s subtitles" % langName(lang['code']).lower()
                subDownloads = downloadSub(myFile, lang['code'], path, verbose)
    else:
        print "--- Getting %s subs" % langName(getSubs).lower()
        subNameLang = "%s.%s.%s" % (subName, getSubs, "srt")
        if os.path.isfile(subNameLang):
            print "--- Already has %s subtitles" % langName(getSubs).lower()
            subDownloads = foundLang("%s - present" % getSubs)
        else:
            print "*** Has no %s subtitles" % langName(getSubs).lower()
            subDownloads = downloadSub(myFile, getSubs, path, verbose)
        
    os.chdir(origWD)  # change working directory back
    return subDownloads

def downloadSub(myFile, lang, path, verbose):
    cli = False
    print "--- Trying to download..."
    origWD = os.getcwd()  # current working directory
    os.chdir(path)  # change working directory to where the videos are
    if cli == True:
        # old subliminal:
        #if call(["subliminal", "-q", "-l", lang, "--", myFile]):  # try to download the subtitles
        # new subliminal
        if call(["subliminal", "download", "-l", lang, "--", myFile]):  # try to download the subtitles
            print "*** Could not find %s subtitles" % langName(lang).lower()
            subDownloads = foundLang("%s - not found" % lang)
        else:
            print "--- Downloaded %s subtitles" % langName(lang).lower()
            subDownloads = foundLang(lang)  # sending language code to be added
            # subName = "%s.%s.%s" % (os.path.splitext(myFile)[0], lang, "srt")
    else:
        video = Video.fromname(myFile)
        if verbose:
            print "--- Checking subtititles for \n    %s" % video
        # configure the cache
        #region.configure('dogpile.cache.dbm', arguments={'filename': 'cachefile.dbm'})
        my_region = region.configure('dogpile.cache.memory', arguments={'filename': 'cachefile.dbm'}, replace_existing_backend=True)
        if verbose:
            print "--- Searching for best subtitle..."
        #best_subtitles = download_best_subtitles([video], {lang}, providers=['podnapisi'])
        best_subtitles = download_best_subtitles([video], {lang}, providers=['podnapisi', 'opensubtitles', 'addic7ed'])
        #best_subtitles = download_best_subtitles([video], {lang})
        try:
            best_subtitle = best_subtitles[video][0]
        except:
            print "*** Could not find %s subtitles" % langName(lang).lower()
            subDownloads = foundLang("%s - not found" % lang)
        else:
            print "--- Downloaded %s subtitles" % langName(lang).lower()
            #if verbose:
            #    print "--- Score for this subtitle is %s" % compute_score(best_subtitle, video)
            subDownloads = foundLang(lang)  # sending language code to be added
            if verbose:
                print "--- Saving subtitles..."
            save_subtitles(video, [best_subtitle])
    os.chdir(origWD)  # change working directory back
    return subDownloads

def compareCodes(existingCode, checkedCode, myFile, ask):
    setCode = existingCode
    
    print "existing: %s   checked: %s" % (existingCode, checkedCode)

    if ask:
        askForCode(existingCode, checkedCode, myFile)
    elif existingCode == checkedCode:  # set code and detected codes match
        print "--- detectlanguage.com agrees"
    else:  # set code and detected codes does not match 
        print "*** detectlanguage.com disagrees"
        print "\n    %s" % myFile
        setCode = askForCode(existingCode, checkedCode, myFile)
                
    return setCode

def askForCode(existingCode, checkedCode, myFile):
    print "    Existing code is %s - %s, and checked code is %s - %s\n" % (existingCode, langName(existingCode).lower(), checkedCode, langName(existingCode).lower())

    print "    1 - Save as is: %s - %s" % (existingCode, langName(existingCode).lower())
    print "    2 - Change to detected code: %s - %s" % (checkedCode, langName(checkedCode).lower())
    print "    3 - Set to new code"

    while True:
        choice = raw_input("\n    Your choice: ")  # get choice
        if choice == "1":
            print "--- Keeping existing code %s" % existingCode
            setCode = existingCode
            break
        elif choice == "2":
            print "--- Setting language code to %s" % checkedCode
            changeCode(myFile, checkedCode)  # change code to the detected one
            setCode = checkedCode
            break
        elif choice == "3":
            while True:
                newCode = raw_input("\n    Enter new code: ")  # type in code
                for language in languages:  # run through codes to find if typed one is allowed
                    if newCode == language['code']:  # typed code is allowed
                        allowed = True
                        break
                    else:  # typed code is not allowed
                        allowed = False
                if allowed:  # typed code is allowed
                    break
                else:  #  # typed code is not allowed
                    print "\n    %s not a valid language code" % newCode
            changeCode(myFile, newCode)  # change code to your input
            setCode = newCode
            break
        else:
            print "\n    Not a valid choice"
            
    return setCode

def findVideoFiles(searchPath, recursive, videoFiles, verbose):
    num = 0
    
    if recursive:  # scan directories recursively
        print "\n--- Searching %s recursively for video files..." % searchPath
        for root, dirs, files in os.walk(searchPath):
            for myFile in files:
                videoFound = False
                for extension in videoExtensions:
                    if isVideo(os.path.join(str(root), myFile), extension):  # check if myFile matches any of the video extensions
                        print "%s" % myFile
                        num += 1
                        videoFound = True
                        break
                if videoFound:
                    videoFiles.append(os.path.join(str(root), myFile))
    else:
        print "\n--- Searching %s for video files..." % searchPath
        for myFile in os.listdir(searchPath):
            videoFound = False
            for extension in videoExtensions:
                if isVideo(os.path.join(str(searchPath), myFile), extension):  # check if myFile matches any of the video extensions
                    print "%s" % myFile
                    num += 1
                    videoFound = True
                    break
            if videoFound:
                videoFiles.append(os.path.join(str(searchPath), myFile))
                
    print "--- Number of video files in %s: %d\n" % (searchPath, num)
    
    return sorted(videoFiles)

def findSubFiles(searchPath, recursive, extension, subFiles, findCode, verbose):
    num = 0
    
    if recursive:  # scan directories recursively
        print "\n--- Searching %s recursively for files ending with %s" % (searchPath, extension)
        if findCode:
            print "with language code %s..." % findCode
        for root, dirs, files in os.walk(searchPath):
            for myFile in files:
                if isSub(os.path.join(str(root), myFile), extension, verbose):  # check if myFile matches criteria
                    print "%s" % myFile
                    num += 1
                    subFiles.append(os.path.join(str(root), myFile))
                    
    else:  # scan single directory
        print "\n--- Searching %s for files ending with %s" % (searchPath, extension)
        if findCode:
            print "with language code %s..." % findCode
        for myFile in os.listdir(searchPath):
            if isSub(os.path.join(str(searchPath), myFile), extension, verbose):  # check if myFile matches criteria
                print "%s" % myFile
                num += 1
                subFiles.append(os.path.join(str(searchPath), myFile))
                
    print "--- Number of subtitle files in %s: %d\n" % (searchPath, num)

    return sorted(subFiles)

def continueWithProcess(myFile, keepOld, reDownload, verbose):
    number = 0
    continueProcess = True
    
    fileName = os.path.splitext(myFile)[0]
    suffix = os.path.splitext(myFile)[1].lstrip(".")
    
    if os.path.isfile("%s.%s" % (fileName, suffix)):
        print("*** %s.%s already exists" % (fileName, suffix))
        continueProcess = False
        if reDownload:
            os.remove("%s.%s" % (fileName, suffix))
            continueProcess = True
        elif keepOld:
            while True:
                number += 1
                print(("--- Renaming it to %s.%s.old%s"
                       % (fileName, suffix, number)))
                print
                if os.path.isfile("%s.%s.old%s" % (fileName, suffix, number)):
                    print("*** %s.%s.old%s already exists" % (fileName, suffix, number))
                else:
                    os.rename("%s.%s" % (fileName, suffix),
                              "%s.%s.old%s" % (fileName, suffix, number))
                    continueProcess = True
                    break
        else:
            continueProcess = False
            
    return continueProcess

def runProcess(cmd, verbose):
    if verbose:
        print "Command: %s\n" % cmd
                        
    args = shlex.split(cmd)
    
    process = Popen(args, stdout=PIPE)    
    process.communicate() 
    exitCode = process.wait()

    if verbose:
        print "Exit code: %s" % exitCode
 
    return exitCode

def runProcessReturnOutput(cmd, verbose):
    if verbose:
        print "Command: %s\n" % cmd
                        
    args = shlex.split(cmd)
    
    process = Popen(args, stdout=PIPE)    
    output = process.communicate() 
    exitCode = process.wait()

    if verbose:
        print "Output from command:"
        print output
        print "Exit code: %s" % exitCode
 
    return output
    
    
    
    
    
    
    
    
    
    
    
    
    
    
