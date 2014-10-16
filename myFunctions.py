#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import re, sys, ConfigParser, os, detectlanguage, codecs, pysrt

from itertools import islice
from sys import exit
#from string import digits
#from collections import namedtuple
from subprocess import call
from BeautifulSoup import BeautifulSoup #, UnicodeDammit
from pycaption import detect_format, SRTWriter, SAMIReader, DFXPReader, CaptionConverter # SRTReader
from shutil import copyfile

# libraries for subliminal
#from __future__ import unicode_literals  # python 2 only
#from babelfish import Language
#from datetime import timedelta
#import subliminal

# starting up some variables
#num = 0
searchPath = ""
searchPathRecursive = ""
extension = ""
langSums = []

config = ConfigParser.ConfigParser()
config.read("%s/config.ini" % os.path.dirname(__file__)) # read config file

##### mainly for subGetLangs #####
prefLangs = (config.get('languages','prefLangs')).split(',') # prefered languages

detectRows = int(config.get('variables','detectRows')) # number of rows sent to detectlanguage.com in each trys
detectTrys = int(config.get('variables','detectTrys')) # number of trys to detect language at detectlanguage.com

detectlanguage.configuration.api_key = config.get('detectlanguage_com','api-key') # api-key to detectlanguage.com from config file

languages = detectlanguage.languages() # get available languages from detectlanguage.com

languages.append({u'code': u'xx', u'name': u'UNKNOWN'})

prefEncoding = config.get('coding','prefEncoding') # your preferred file encoding

debug = int(config.get('misc','debug'))

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
    elif errorCode in (6, 7):
        print "%s is not a valid argument" % extra
        usage(errorCode)
    else:
        print "\nError: Unknown"

def usage(exitCode):
    print "\nUsage:"
    print "----------------------------------------"
    print "%s -l [-p <path>] [-r] [-e <extension>]" % sys.argv[0]
    print "          Find files, set language code if none, and create symbolic 'l'ink to them without language code"
    print "          Options: Set -e <extension> to set 's'uffix to search for"
    print "                   Set -r to search 'r'ecursively"
    print "                   Set -p <path> to set other 'p'ath than current"
    print "     OR\n"
    print "%s -d" % sys.argv[0]
    print "          Get available languages from 'd'etectlanguage.com, and your account status at the same place"
    print "     OR\n"
    print "%s -g [-p <path>] [-r] [-e <extension>]" % sys.argv[0]
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
    print "          Options: Set -e <extension> to set 's'uffix to search for"
    print "                   Set -r to search 'r'ecursively"
    print "                   Set -p <path> to set other 'p'ath than current"
    print "     OR\n"
    print "%s -f [-k] [-p <path>] [-r] [-e <extension>]" % sys.argv[0]
    print "          Find subtitles, check 'f'ormat, and convert to UTF8, and convert to srt"
    print "          Options: Set -k to 'k'eep temporary file"
    print "                   Set -e <extension> to set 's'uffix to search for"
    print "                   Set -r to search 'r'ecursively"
    print "                   Set -p <path> to set other 'p'ath than current"
    print "     OR\n"
    print "%s -s [list|convert] [-p <path>] [-r]" % sys.argv[0]
    print "          Arguments: list only lists subtitles files"
    print "                     convert also converts the to srt-format if possible"
    print "          Options: 'S'earch for posibble subtitles files"
    print "                   Set -r to search 'r'ecursively"
    print "                   Set -p <path> to set other 'p'ath than current"
    print "%s -h" % sys.argv[0]
    print "          Prints this"
    print "\n"
    sys.exit(exitCode)

##### mainly for downloadSubs #####
dbmCacheFile = "%s/%s/cachefile.dbm" % (os.path.expanduser("~"), config.get('video','dbmCacheFile')) # get location for dbm cache file

videoExtensions = (config.get('video','videoExtensions')).split(',') # load video extensions

def isSub(myFile, extension, verbose): # returns True if extension is correct, is a file, is not a link and is not empty
    result = False # set default result False
    #if verbose:
    #    print "--- Checking if %s matches our criteria" % myFile
    fileExtension = os.path.splitext(myFile)[1] # get extension only with the leading punctuation
    if fileExtension.lower() == extension and os.path.isfile(myFile) and not os.path.islink(myFile): # file ends with correct extension, is a file and is not a link
        if fileEmpty(myFile): # myFile is empty
            print "\n%s" % myFile
            print "*** File is empty. Deleting it..."
            os.remove(myFile)
        else:
            result = True # myFile ends with correct extension, is a file, is not a link and is empty
    return result

def hasLangCode(myFile): # returns the language code present, if there is one. Otherwise returns empty
    result = "" # default return code
    fileName = os.path.splitext(myFile)[0] # myFile name without punctuation and extension
    for language in languages:
        if '.%s' % language['code'] == os.path.splitext(fileName)[1]: # adds punctuation before code, and compares to extension in stripped file name. If same, returns code
            result = language # set detected language code to result
    return result # return detected language code

def fileFound(myFile, langSums, verbose): # runs on every file that matches extension, is not a link and is not empty
    acceptUnreliable = config.get('variables','acceptUnreliable') # True if we accept unreliable as language code
    codePresent = hasLangCode(myFile) # check if the file already has a language code. Returns code if there is one, otherwise empty

    if not codePresent: # file name has no language code
        checkCode = checkLang(myFile, verbose) # determine what language file has. Returns language code
        if acceptUnreliable: # we accept "unreliable" as language code
            addLangCode(myFile, checkCode) # add language code to file name
            langSums = foundLang(checkCode) # sending language code to be added if code was not present and we accept "xx" as language code
        else: # we don't accept "xx" as language code
            if checkCode != "xx": # if the language code is reliable
                addLangCode(myFile, checkCode) # add language code to file name
            else:
                print "*** Can't determine if language code present is correct. Doing nothing further"

    else: # file name has language code
        print "*** Already has language code %s - %s" % (codePresent['code'], codePresent['name'].lower())
        langSums = foundLang(codePresent['code']) # sending language code to be added if language code was present

        if hasLink(myFile) and codePresent != "xx": # file has link and language code is not xx
            print "*** Already has link"
            if codePresent['code'] == prefLangs[0]: # language code for this file is your first prefered one
                print "--- Language code for this file is %s. Creating new link anyway" % prefLangs[0]
                makeLink(myFile) # create a link to the file

        elif codePresent == "xx": # language code is "xx"
            checkCode = checkLang(myFile, verbose) # determine what language file has at detectlanguage.com. Returns language code

            if acceptUnreliable: # we accept "xx" as language code
                if checkCode == codePresent['code']: # correct language code already set
                    print "--- Present language code seems correct!"
                    makeLink(myFile) # create a link to the file
                else: # wrong code set to file
                    print "*** Present language code don't seem correct. Changing %s to %s" % (codePresent['code'], checkCode) 
                    myFile = changeCode(myFile, checkCode) # set correct language code to myFile, and get the new file name
                    makeLink(myFile) # create a link to the file
            else: # we don't accept "xx" as language code
                if checkCode == "xx": # language result is unknown
                    print "*** Can't determine if language code present is correct. Doing nothing further"
                else: # if the the result is reliable
                    if checkCode == codePresent: # correct language code already set
                        print "--- Present language code seems correct!"
                    else: # wrong code set to file
                        print "*** Present language code don't seem correct. Changing %s to %s" % (codePresent['code'], checkCode)
                        myFile = changeCode(myFile, checkCode) # set correct language code to myFile, and get the new file name
                        makeLink(myFile) # create a link to the file, if it already has correct language code

        else:
            makeLink(myFile) # create a link to the file
            #langSums = foundLang(codePresent['code']) # sending language code to be added
    return langSums

def makeLink(myFile): # create a link to file that has language code
    print "--- Creating link"
    linkName = "%s%s" % (os.path.splitext(os.path.splitext(myFile)[0])[0], os.path.splitext(myFile)[1]) # remove extension, remove another extension and add first extension again
    if os.path.isfile(linkName) and not os.path.islink(linkName): # the new link would overwrite a file
        print "*** %s is a file. Skipping" % linkName
    else:
        if os.path.islink(linkName): # the new link would overwrite an old link
            print "*** %s exists as a link. Removing it..." % linkName
            os.unlink(linkName) # delete old link
        print "--- Creating new link"
        os.symlink(os.path.basename(myFile), linkName) # create a link pointing to the file with link name without language code
    return

def addLangCode(myFile, langCode): # adds language code to file name
    print "--- Adding language code to %s" % myFile
    # takes filename without extension, adds punctuation and language code and adds the old extension
    newName = "%s.%s%s" % (os.path.splitext(myFile)[0], langCode, os.path.splitext(myFile)[1])
    if os.path.isfile(newName): # new file name exists as a file
        print "*** %s already exist. Skipping..." % newName
    else:
        print "--- Renaming to %s" % newName
        os.rename(myFile, newName) # rename the file
        makeLink(newName) # make link to file

def checkLang(myFile, verbose): # checks file for language and returns language code, or if is doubtful returns "xx"
    tryNumber = 0 # starting up counter
    finished = False
    status = detectlanguage.user_status() # get status for the account at detectlanguage.com
    if status['status'] == "SUSPENDED":
        print "*** Account at detectlanguage.com is suspended"
        print "    Run %s -d to see status" % sys.argv[0]
        print "    Quitting...\n"
        exit(7)
    with open(myFile) as theFile:
        fileLines = sum(1 for line in theFile) # number of lines in file
    theFile.close() # close file
    while True:
        if tryNumber * detectRows >= fileLines:
            print "*** File only has %d lines. No more lines to send. Accepting answer" % fileLines
            break

        with open(myFile) as theFile: # open file
            head = list(islice(theFile, tryNumber * detectRows, (tryNumber + 1) * detectRows)) # select rows from file
        theFile.close() # close file

        text = convertText(head, verbose) # convert all strange characters, remove special characters and so on

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

def changeCode(myFile, newCode): # change language code to newCode
    newName = "%s.%s%s" % (os.path.splitext(os.path.splitext(myFile)[0])[0], newCode, os.path.splitext(myFile)[1]) # file name without punctuation and last two extensions
    print "--- Renaming to %s" % newName
    os.rename(myFile, newName) # rename the file
    return newName

def hasLink(myFile): # return True if the file already has a link to it, excluding the language code
    result = False
    linkName = "%s%s" % (os.path.splitext(os.path.splitext(myFile)[0])[0], os.path.splitext(myFile)[1])
    if os.path.islink(linkName): # there is a link to the file
        result = True
    return result

def fileEmpty(myFile): # returns True is file is empty
    return os.stat(myFile).st_size==0

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

def convertText(head, verbose):
        text = ""
        textc = []
        textd = []
        
        if debug:
            print "\nhead:"
            print "-" * 40
            print head
            print "-" * 40
            
        texta = str(head) # make string of array
        if debug:
            print "\nstring:"
            print "-" * 40
            print texta
            print "-" * 40
            
        textb = texta.split("\\n', '") # split string into list
        if debug:
            print "\nsplit:"
            print "-" * 40
            for line in textb:
                print line
            print "-" * 40
        
        for line in textb: # process line by line, deleting all unwanted ones
            if (
                not line == "\\r\\n']" 
                and not line == "['1" 
                and not line == '"]' 
                and not re.match("^[0-9:',.>'\- \]]*$", line)
                ) :
                textc.append(line)

        for line in textc: # append to text, converting all odd things...
            textd.append(line.
                         replace('\\xc3\\xa5','å').
                         replace('\\xc3\\xa4','ä').
                         replace('\\xc3\\xb6','ö').
                         replace('\\xc3\\x85', 'Å').
                         replace('\\xc3\\x84', 'Ä').
                         replace('\\xc3\\x96', 'Ö').
                         rstrip('\-').lstrip('\-').
                         lstrip("', '").lstrip("- ").
                         lstrip('"- ').lstrip(", '").
                         lstrip('"- ').rstrip("\\n']").
                         rstrip(" ")
                         )

        for line in textd:
            #print line
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

def hasSub(myFile, path, subDownloads, verbose):
    subName = os.path.splitext(myFile)[0]
    origWD = os.getcwd() # current working directory
    os.chdir(path) # change working directory to where the videos are
    for lang in prefLangs:
        subNameLang = "%s.%s.%s" % (subName, lang, "srt")
        if os.path.isfile(subNameLang):
            print "--- Already has %s subtitles" % langName(lang).lower()
            subDownloads = foundLang("%s - present" % lang)
        else:
            print "*** Has no %s subtitles" % langName(lang).lower()
            subDownloads = downloadSub(myFile, lang, path)
    os.chdir(origWD) # change working directory back
    return subDownloads

def downloadSub(myFile, lang, path):
    print "--- Trying to download..."
    origWD = os.getcwd() # current working directory
    os.chdir(path) # change working directory to where the videos are
    if call(["subliminal", "-q", "-l", lang, "--", myFile]): # try to download the subtitles
        print "*** Could not find %s subtitles" % langName(lang).lower()
        subDownloads = foundLang("%s - not found" % lang)
    else:
        print "--- Downloaded %s subtitles" % langName(lang).lower()
        subDownloads = foundLang(lang) # sending language code to be added
        #subName = "%s.%s.%s" % (os.path.splitext(myFile)[0], lang, "srt")
    os.chdir(origWD) # change working directory back
    return subDownloads

def compareCodes(existingCode, checkedCode, myFile):
    setCode = existingCode
    
    print "existing: %s   checked: %s" % (existingCode, checkedCode)

    if existingCode == checkedCode: # set code and detected codes match
        print "--- detectlanguage.com agrees"
    else: # set code and detected codes does not match 
        print "*** detectlanguage.com disagrees"
        print "\n    %s" % myFile
        print "    Existing code is %s - %s, and checked code is %s - %s\n" % (existingCode, langName(existingCode).lower(), checkedCode, langName(existingCode).lower())

        print "    1 - Save as is: %s - %s" % (existingCode, langName(existingCode).lower())
        print "    2 - Change to detected code: %s - %s" % (checkedCode, langName(checkedCode).lower())
        print "    3 - Set to new code"

        while True:
            choice = raw_input("\n    Your choice: ") # get choice
            if choice == "1":
                print "--- Keeping existing code %s" % existingCode
                setCode = existingCode
                break
            elif choice == "2":
                print "--- Setting language code to %s" % checkedCode
                changeCode(myFile, checkedCode) # change code to the detected one
                setCode = checkedCode
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
                changeCode(myFile, newCode) # change code to your input
                setCode = newCode
                break
            else:
                print "\n    Not a valid choice"
                
    return setCode

def checkCoding(myFile, verbose):
    theFile = open(myFile) # open sub
    soup = BeautifulSoup(theFile) # read sub into BeautifulSoup
    theFile.close() # close sub
    encoding = soup.originalEncoding # let soup detect encoding
    if verbose:
        print "--- BeautifulSoup says: %s" % encoding
    if encoding == "ISO-8859-2":
        print "*** Detected ISO-8859-2. Assuming it's ISO-8859-1"
        encoding = "ISO-8859-1"
    elif encoding == "windows-1251":
        #print "*** Detected windows-1251. Assuming it's cp1251"
        #encoding = "cp1251"
        print "*** Detected windows-1251. Assuming it's ISO-8859-1"
        encoding = "ISO-8859-1"
    return encoding

def changeEncoding(myFile, encoding, keep, verbose):
    if verbose:
        print "--- Renaming to %s.%s" % (myFile, encoding)
    os.rename(myFile, "%s.%s" % (myFile, encoding))
    print "--- Changing encoding to %s" % prefEncoding
    blockSize = 1048576 # size in bytes to read every chunk
    with codecs.open("%s.%s" % (myFile, encoding), "r", encoding) as sourceFile: # open the copy as source
        with codecs.open(myFile, "w", prefEncoding) as targetFile: # open the target
            while True:
                contents = sourceFile.read(blockSize)
                if not contents:
                    break
                if verbose:
                    print "--- Writing %s" % myFile
                targetFile.write(contents) # write chunk to target
    sourceFile.close() # close source
    targetFile.close() # close target
    if not keep:
        if verbose:
            print "--- Deleting temporary file %s.%s" % (myFile, encoding)
        os.remove("%s.%s" % (myFile, encoding))

def checkFormat(myFile, verbose):
    myFormat = ""
    if verbose:
        print "--- Checking subtitle format"
    capsFile = open(myFile) # open sub
    caps = capsFile.read() # read sub
    reader = detect_format(caps) # detect format with pycaption
    if verbose:
        print "--- pycaption says: %s" % reader
    if reader:
        if "srt" in str(reader):
            myFormat = "srt"
        elif "sami" in str(reader):
            myFormat = "sami"
        elif "dfxp" in str(reader):
            myFormat = "dfxp"
    capsFile.close() # close sub
    return myFormat

def samiToSrt(myFile, keep, verbose):
    if verbose:
        print "--- Renaming to %s.sami" % myFile
    os.rename(myFile, "%s.sami" % myFile)
    print "--- Converting to srt"
    sourceFile = open("%s.sami" % myFile) # open copy as source
    caps = sourceFile.read() # read source
    converter = CaptionConverter() # set pycaptions converter
    converter.read(caps, SAMIReader()) # read sami
    with open(myFile, "w") as targetFile: # open target
        targetFile.write(converter.write(SRTWriter())) # write target
    sourceFile.close() # close source
    targetFile.close() # close target
    if not keep:
        if verbose:
            print "--- Deleting temporary file %s.sami" % myFile
        os.remove("%s.sami" % myFile)

def dfxpToSrt(myFile, keep, verbose):
    if verbose:
        print "--- Renaming to %s.dfxp" % myFile
    os.rename(myFile, "%s.dfxp" % myFile)
    print "--- Converting to srt"
    sourceFile = open("%s.dfxp" % myFile) # open copy as source
    caps = sourceFile.read() # read source
    converter = CaptionConverter() # set pycaptions converter
    converter.read(caps, DFXPReader()) # read sami
    with open(myFile, "w") as targetFile: # open target
        targetFile.write(converter.write(SRTWriter())) # write target
    sourceFile.close() # close source
    targetFile.close() # close target
    if not keep:
        if verbose:
            print "--- Deleting temporary file %s.dfxp" % myFile
        os.remove("%s.dfxp" % myFile)

def emptyEntries(myFile, keep, verbose):
    emptyEntryFound = False
    emptyEntries = 0
    entriesToDelete = []

    if verbose:
        print "--- Searching for empty entries"
    subs = pysrt.open(myFile, encoding='utf-8') # open sub with pysrt as utf-8
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
                print "--- Copying original file to %s.emptyEntries" % myFile
            copyfile(myFile, "%s.emptyEntries" % myFile)
            
        subs.save(myFile, encoding='utf-8') # save sub

        subs = pysrt.open(myFile, encoding='utf-8') # open new sub with pysrt
        entries = len(subs) # count entries
        print "--- Now has %s entries" % entries
        
    return emptyEntryFound

def numbering(myFile, keep, verbose):
    wrongNumbering = False

    if verbose:
        print "--- Checking numbering"

    subs = pysrt.open(myFile, encoding='utf-8') # open sub with pysrt as utf-8
    entries = len(subs) # count entries

    for entryNo in range(0, entries): # count entry numbers up to number of entries
        subEntry = "%s" % subs[entryNo] # read single entry
        lines = subEntry.split('\n') # split entry into lines
        if entryNo + 1 != int(lines[0]): # entry number does not match real numbering
            wrongNumbering = True
            print "*** Correcting numbering"
            copyfile(myFile, "%s.wrongNumbering" % myFile)
            break

    if wrongNumbering:
        targetFile = codecs.open(myFile, "w", prefEncoding)
        subs = pysrt.open("%s.wrongNumbering" % myFile, encoding='utf-8') # open sub with pysrt as utf-8
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
                print "--- Deleting %s.wrongNumbering" % myFile
            os.remove("%s.wrongNumbering" % myFile)

    return wrongNumbering

def findVideoFiles(searchPath, recursive, videoFiles, verbose):
    num = 0
    
    if recursive: # scan directories recursively
        print "\nSearching %s recursively for video files..." % searchPath
        for root, dirs, files in os.walk(searchPath):
            for myFile in files:
                videoFound = False
                for extension in videoExtensions:
                    if isVideo(os.path.join(str(root), myFile), extension): # check if myFile matches any of the video extensions
                        print "%s" % myFile
                        num += 1
                        videoFound = True
                        break
                if videoFound:
                    videoFiles.append(os.path.join(str(root), myFile))
    else:
        print "\nSearching %s for video files..." % searchPath
        for myFile in os.listdir(searchPath):
            videoFound = False
            for extension in videoExtensions:
                if isVideo(os.path.join(str(searchPath), myFile), extension): # check if myFile matches any of the video extensions
                    print "%s" % myFile
                    num += 1
                    videoFound = True
                    break
            if videoFound:
                videoFiles.append(os.path.join(str(searchPath), myFile))
                
    print "Number of video files in %s: %d\n" % (searchPath, num)
    
    return videoFiles

def findSubFiles(searchPath, recursive, extension, subFiles, findCode, verbose):
    num = 0
    
    if recursive: # scan directories recursively
        print "\nSearching %s recursively for files ending with %s" % (searchPath, extension)
        if findCode:
            print "with language code %s..." % findCode
        for root, dirs, files in os.walk(searchPath):
            for myFile in files:
                if isSub(os.path.join(str(root), myFile), extension, verbose): # check if myFile matches criteria
                    print "%s" % myFile
                    num += 1
                    subFiles.append(os.path.join(str(root), myFile))
                    
    else: # scan single directory
        print "\nSearching %s for files ending with %s" % (searchPath, extension)
        if findCode:
            print "with language code %s..." % findCode
        for myFile in os.listdir(searchPath):
            if isSub(os.path.join(str(searchPath), myFile), extension, verbose): # check if myFile matches criteria
                print "%s" % myFile
                num += 1
                subFiles.append(os.path.join(str(searchPath), myFile))
                
    print "Number of subtitle files in %s: %d\n" % (searchPath, num)

    return subFiles