#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import re, sys, ConfigParser, os, detectlanguage, codecs, codecs, pysrt

from itertools import islice
from sys import exit
from string import digits
from collections import namedtuple
from subprocess import call
from BeautifulSoup import BeautifulSoup, UnicodeDammit
from pycaption import detect_format, SRTReader, SRTWriter, SAMIReader, SAMIWriter, CaptionConverter
from shutil import copyfile

# libraries for subliminal
#from __future__ import unicode_literals  # python 2 only
from babelfish import Language
from datetime import timedelta
import subliminal

# starting up some variables
#num = 0
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

prefEncoding = config.get('coding','prefEncoding') # your preferrd file encoding

def onError(errorCode, extra):
    print "\nError:"
    if errorCode == 1:
        print extra
        usage(errorCode)
    elif errorCode == 2:
        print "No options given"
        usage(errorCode)
    elif errorCode == 3:
        print "No program part chosen"
        usage(errorCode)
    elif errorCode == 4:
        print "%s is not a valid path\n" % extra
        sys.exit(4)
    elif errorCode == 5:
        print "Wrong set of options given"
        usage(errorCode)
    elif errorCode == 6:
        print "%s is not a valid argument" % extra
        usage(errorCode)
    else:
        print "\nError: Unknown"

def usage(exitCode):
    print "\nUsage:"
    print "----------------------------------------"
    print "%s -l [-p <path>] [-r] [-s <suffix>]" % sys.argv[0]
    print "          Find files, set language code if none, and create symbolic 'l'ink to them without language code"
    print "          Options: Set -s <suffix> to set 's'uffix to search for"
    print "                   Set -r to search 'r'ecursively"
    print "                   Set -p <path> to set other 'p'ath than current"
    print "     OR\n"
    print "%s -d" % sys.argv[0]
    print "          Get available languages from 'd'etectlanguage.com, and your account status at the same place"
    print "     OR\n"
    print "%s -g [-p <path>] [-r] [-s <suffix>]" % sys.argv[0]
    print "          Search video files, check if there are any srt subtitle files with language code in the name"
    print "          If not try to find and 'g'et subtitles in any of your preferred languages"
    print "          Options: Set -r to search 'r'ecursively"
    print "                   Set -p <path> to set other 'p'ath than current"
    print "     OR\n"
    print "%s -c [all|pref|<code>] [-p <path>] [-r]" % sys.argv[0]
    print "          'C'heck language codes set in filenames manually"
    print "          Arguments: all checks all files with languagecode set"
    print "                     pref checks all files with any of your preferred languages"
    print "                     <code>, give a valid language code"
    print "          Options: Set -s <suffix> to set 's'uffix to search for"
    print "                   Set -r to search 'r'ecursively"
    print "                   Set -p <path> to set other 'p'ath than current"
    print "     OR\n"
    print "%s -f [-k] [-p <path>] [-r] [-s <suffix>]" % sys.argv[0]
    print "          Find subtitles, check 'f'ormat, and convert to UTF8, and convert to srt"
    print "          Options: Set -k to 'k'eep temporary file"
    print "                   Set -s <suffix> to set 's'uffix to search for"
    print "                   Set -r to search 'r'ecursively"
    print "                   Set -p <path> to set other 'p'ath than current"
    print "%s -h" % sys.argv[0]
    print "          Prints this"
    print "\n"
    sys.exit(exitCode)

##### mainly for downloadSubs #####
dbmCacheFile = "%s/%s/cachefile.dbm" % (os.path.expanduser("~"), config.get('video','dbmCacheFile')) # get location for dbm cache file

videoSuffixes = (config.get('video','videoSuffixes')).split(',') # load video suffixes

def isFile(file, suffix, verbose): # returns True if suffix is correct, is a file, is not a link and is not empty
    result = False # set default result False
    #if verbose:
    #    print "--- Checking if %s matches our criteria" % file
    fileExtension = os.path.splitext(file)[1] # get extension only with the leading punctuation
    if fileExtension.lower() == suffix and os.path.isfile(file) and not os.path.islink(file): # file ends with correct suffix, is a file and is not a link
        if fileEmpty(file): # file is empty
            print "\n%s" % file
            print "*** File is empty. Deleting it..."
            os.remove(file)
        else:
            result = True # file ends with correct suffix, is a file, is not a link and is empty
    return result

def hasLangCode(file): # returns the language code present, if there is one. Otherwise returns empty
    result = "" # default return code
    fileName = os.path.splitext(file)[0] # file name without punctuation and suffix
    for language in languages:
        if '.%s' % language['code'] == os.path.splitext(fileName)[1]: # adds punctuation before code, and compares to suffix in stripped file name. If same, returns code
            result = language # set detected language code to result
    return result # return detected language code

def fileFound(file, langSums, verbose): # runs on every file that matches suffix, is not a link and is not empty
    acceptUnreliable = config.get('variables','acceptUnreliable') # True if we accept unreliable as language code
    codePresent = hasLangCode(file) # check if the file already has a language code. Returns code if there is one, otherwise empty

    if not codePresent: # file name has no language code
        checkCode = checkLang(file, verbose) # determine what language file has. Returns language code
        if acceptUnreliable: # we accept "unreliable" as language code
            addLangCode(file, checkCode) # add language code to file name
            langSums = foundLang(checkCode) # sending language code to be added if code was not present and we accept "xx" as language code
        else: # we don't accept "xx" as language code
            if checkCode != "xx": # if the language code is reliable
                addLangCode(file, checkCode) # add language code to file name
            else:
                print "*** Can't determine if language code present is correct. Doing nothing further"

    else: # file name has language code
        print "*** Already has language code %s - %s" % (codePresent['code'], codePresent['name'].lower())
        langSums = foundLang(codePresent['code']) # sending language code to be added if language code was present

        if hasLink(file) and codePresent != "xx": # file has link and language code is not xx
            print "*** Already has link"
            if codePresent['code'] == prefLangs[0]: # language code for this file is your first prefered one
                print "--- Language code for this file is %s. Creating new link anyway" % prefLangs[0]
                makeLink(file) # create a link to the file

        elif codePresent == "xx": # language code is "xx"
            checkCode = checkLang(file, verbose) # determine what language file has at detectlanguage.com. Returns language code

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

def checkLang(file, verbose): # checks file for language and returns language code, or if is doubtful returns "xx"
    status = detectlanguage.user_status() # get status for the account at detectlanguage.com
    tryNumber = 0 # starting up counter
    finished = False
    if status['status'] == "SUSPENDED":
        print "*** Account at detectlanguage.com is suspended"
        print "    Run %s -d to see status" % sys.argv[0]
        print "    Quitting...\n"
        exit(7)
    with open(file) as myfile:
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

        if verbose:
            print "\n%s\n" % text

        print "--- Sending rows %d-%d to detectlanguage.com" % (tryNumber * detectRows, (tryNumber + 1) * detectRows)
        result = detectlanguage.detect(text) # detect language

        if result[0]['isReliable']: # result is reliable
            langCode = str(result[0]['language']) # langCode set to answer from detectlanguage.com
            print "--- Got %s - %s" % (langCode, langName(langCode))

            for lang in prefLangs: # run through the prefered languages
                if lang == langCode: # recieved language is one of the prefered languages
                    finished = True # search for language code is finished
                    break # break out of this for loop

            if finished:
                break # break out of the while loop
            else:
                print "*** Not one of your prefered languages"
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
    result = ""
    for lang in languages:
        if langCode == lang['code']:
            result = lang['name']
            break
    return result

def foundLang(langCode): # add language code to langSums
    langSums.append(langCode)    
    return langSums

def convertText(head):
        texta = str(head) # make string of array
        textb = texta.split("\\r\\n")
        
        textc = []
        textd = []
        text = ""
        for line in textb:
            if not line == "\\r\\n']" and not line == "['1" and not line == '"]' and not re.match("^[0-9:',.>'\- \]]*$", line):# re.match("^[0-9:\-.>\' ]*$", line):
                #print line
                textc.append(line)

        for line in textc:
            textd.append(line.replace('\\xc3\\xa5','å').replace('\\xc3\\xa4','ä').replace('\\xc3\\xb6','ö').replace('\\xc3\\x85', 'Å').replace('\\xc3\\x84', 'Ä').replace('\\xc3\\x96', 'Ö').rstrip('\-').lstrip('\-').lstrip("', '").lstrip("- ").lstrip('"- ').lstrip(", '").lstrip('"- '))
            #textd.append(line.replace('\\xc3\\xa5','å').replace('\\xc3\\xa4','ä').replace('\\xc3\\xb6','ö').replace('\\xc3\\x85', 'Å').replace('\\xc3\\x84', 'Ä').replace('\\xc3\\\x96', 'Ö').rstrip('\-').lstrip('\-').lstrip("'").lstrip(",").lstrip('"'))
        for line in textd:
            #print line
            text = "%s %s" % (text, line)


        return text

def isVideo(file, suffix):
    result = False
    fileExtension = os.path.splitext(file)[1]
    if fileExtension.lower() == ".%s" % suffix:
        result = True
    return result

def hasSub(file, path):
    subName = os.path.splitext(file)[0]
    origWD = os.getcwd() # current working directory
    os.chdir(path) # change working directory to where the videos are
    for lang in prefLangs:
        subNameLang = "%s.%s.%s" % (subName, lang, "srt")
        if os.path.isfile(subNameLang):
            print "--- Already has %s subtitles" % langName(lang).lower()
            subDownloads = foundLang("%s - present" % lang)
        else:
            print "*** Has no %s subtitles" % langName(lang).lower()
            subDownloads = downloadSub(file, lang, path)
    os.chdir(origWD) # change working directory back
    return subDownloads

def downloadSub(file, lang, path):
    print "--- Trying to download..."
    origWD = os.getcwd() # current working directory
    os.chdir(path) # change working directory to where the videos are
    if call(["subliminal", "-q", "-l", lang, "--", file]): # try to download the subtitles
        print "*** Could not find %s subtitles" % langName(lang).lower()
        subDownloads = foundLang("%s - not found" % lang)
    else:
        print "--- Downloaded %s subtitles" % langName(lang).lower()
        subDownloads = foundLang(lang) # sending language code to be added
        subName = "%s.%s.%s" % (os.path.splitext(file)[0], lang, "srt")
    os.chdir(origWD) # change working directory back
    return subDownloads

def compareCodes(existingCode, checkedCode, file):

    print "existing: %s   checked: %s" % (existingCode, checkedCode)

    if existingCode == checkedCode: # set code and detected codes match
        print "--- detectlanguage.com agrees"
    else: # set code and detected codes does not match 
        print "*** detectlanguage.com disagrees"
        print "\n    %s" % file
        print "    Existing code is %s - %s, and checked code is %s - %s\n" % (existingCode, langName(existingCode).lower(), checkedCode, langName(existingCode).lower())

        print "    1 - Save as is: %s - %s" % (existingCode, langName(existingCode).lower())
        print "    2 - Change to detected code: %s - %s" % (checkedCode, langName(checkedCode).lower())
        print "    3 - Set to new code"

        while True:
            choice = raw_input("\n    Your choice: ") # get choice
            if choice == "1":
                print "--- Keeping existing code %s" % existingCode
                break
            elif choice == "2":
                print "--- Setting language code to %s" % checkedCode
                changeCode(file, checkedCode) # change code to the detected one
                break
            elif choice == "3":
                while True:
                    newCode = raw_input("\n    Enter new code: ") # type in code
                    for language in languages: # run through codes to find if typed one is allowed
                        if newCode == language['code']: # typed code is allowed

                            allowed = True
                            break
                        else: # typed code is not allowed
                            allowed = False
                    if allowed: # typed code is allowed
                        break
                    else: #  # typed code is not allowed
                        print "\n    %s not a valid language code" % newCode
                changeCode(file, newCode) # change code to your input
                break
            else:
                print "\n    Not a valid choice"

def checkCoding(file):
    myFile = open(file) # open sub
    soup = BeautifulSoup(myFile) # read sub into BeautifulSoup
    myFile.close() # close sub
    encoding = soup.originalEncoding # let soup detect encoding
    if encoding == "ISO-8859-2":
        print "*** Detected ISO-8859-2. Assuming it's ISO-8859-1"
        encoding = "ISO-8859-1"
    elif encoding == "windows-1251":
        #print "*** Detected windows-1251. Assuming it's cp1251"
        #encoding = "cp1251"
        print "*** Detected windows-1251. Assuming it's ISO-8859-1"
        encoding = "ISO-8859-1"
    return encoding

def changeEncoding(file, encoding, keep, verbose):
    if verbose:
        print "--- Renaming to %s.%s" % (file, encoding)
    os.rename(file, "%s.%s" % (file, encoding))
    print "--- Changing encoding to %s" % prefEncoding
    blockSize = 1048576 # size in bytes to read every chunk
    with codecs.open("%s.%s" % (file, encoding), "r", encoding) as sourceFile: # open the copy as source
        with codecs.open(file, "w", prefEncoding) as targetFile: # open the target
            while True:
                contents = sourceFile.read(blockSize)
                if not contents:
                    break
                if verbose:
                    print "--- Writing %s" % file
                targetFile.write(contents) # write chunk to target
    sourceFile.close() # close source
    targetFile.close() # close target
    if not keep:
        if verbose:
            print "--- Deleting temporary file %s.%s" % (file, encoding)
        os.remove("%s.%s" % (file, encoding))

def checkFormat(file, verbose):
    if verbose:
        print "--- Checking subtitle format"
    capsFile = open(file) # open sub
    caps = capsFile.read() # read sub
    reader = detect_format(caps) # detect format with pycaption
    if reader:
        if "srt" in str(reader):
            format = "srt"
        elif "sami" in str(reader):
            format = "sami"
        else:
            format = ""
    capsFile.close() # close sub
    return format

def samiToSrt(file, keep, verbose):
    if verbose:
        print "--- Renaming to %s.sami" % file
    os.rename(file, "%s.sami" % file)
    print "--- Converting to srt"
    sourceFile = open("%s.sami" % file) # open copy as source
    caps = sourceFile.read() # read source
    converter = CaptionConverter() # set pycaptions converter
    converter.read(caps, SAMIReader()) # read sami
    with open(file, "w") as targetFile: # open target
        targetFile.write(converter.write(SRTWriter())) # write target
    sourceFile.close() # close source
    targetFile.close() # close target
    if not keep:
        if verbose:
            print "--- Deleting temporary file %s.sami" % file
        os.remove("%s.sami" % file)

def emptyEntries(file, keep, verbose):
    emptyEntryFound = False
    emptyEntries = 0
    entriesToDelete = []

    if verbose:
        print "--- Searching for empty entries"
    subs = pysrt.open(file, encoding='utf-8') # open sub with pysrt as utf-8
    entries = len(subs) # count entries
    if verbose:
        print "--- %s entries total" % entries

    for entryNo in range(0, entries): # count entry numbers up to number of entries
        subEntry = "%s" % subs[entryNo] # read single entry
        lines = subEntry.split('\n') # split entry into lines
        lineNo = 0 # set first line to 0
        emptyEntry = False

        for row in lines: # read lines one by one
            if lineNo == 2:
                if row == "&nbsp;" or not row: # if third line is &nbsp; or empty
                    emptyEntry = True
            if emptyEntry and lineNo == 3 and row == "": # if third line is &nbsp; and fourth line is empty
                emptyEntryFound = True
                emptyEntries += 1
                entriesToDelete.append(entryNo) # add entry number to list
            lineNo += 1

    if emptyEntryFound: # if empty entry is found
        print "*** %s empty entries found" % emptyEntries

        for entryNo in reversed(entriesToDelete): # run through entry numbers in reverse
            #print lineNo
            del subs[entryNo] # delete entry
            
        if keep:
            if verbose:
                print "--- Copying original file to %s.emptyEntries" % file
            copyfile(file, "%s.emptyEntries" % file)
            
        subs.save(file, encoding='utf-8') # save sub

        subs = pysrt.open(file, encoding='utf-8') # open new sub with pysrt
        entries = len(subs) # count entries
        print "--- Now has %s entries" % entries

def numbering(file, keep, verbose):
    wrongNumbering = False

    if verbose:
        print "--- Checking numbering"

    subs = pysrt.open(file, encoding='utf-8') # open sub with pysrt as utf-8
    entries = len(subs) # count entries

    for entryNo in range(0, entries): # count entry numbers up to number of entries
        subEntry = "%s" % subs[entryNo] # read single entry
        lines = subEntry.split('\n') # split entry into lines
        if entryNo + 1 != int(lines[0]): # entry number does not match real numbering
            wrongNumbering = True
            print "*** Correcting numbering"
            copyfile(file, "%s.wrongNumbering" % file)
            break

    if wrongNumbering:
        targetFile = codecs.open(file, "w", prefEncoding)
        subs = pysrt.open("%s.wrongNumbering" % file, encoding='utf-8') # open sub with pysrt as utf-8
        entries = len(subs) # count entries
        for entryNo in range(0, entries): # count entry numbers up to number of entries
            subEntry = "%s" % subs[entryNo] # read single entry
            lines = subEntry.split('\n') # split entry into lines
            noLines = len(lines) # number of lines in each entry
            for line in range(0, noLines):
                if line == 0:
                    targetFile.write("%s\n" % str(entryNo +1))
                    #print entryNo + 1
                else:
                    targetFile.write("%s\n" % lines[line])
                    #print lines[line]
        targetFile.close()

        if not keep:
            if verbose:
                print "--- Deleting %s.wrongNumbering" % file
            os.remove("%s.wrongNumbering" % file)

    return wrongNumbering
