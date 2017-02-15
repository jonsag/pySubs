#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import os, codecs, pysrt, sys

from BeautifulSoup import BeautifulSoup
from pycaption import detect_format, SRTWriter, SAMIReader, DFXPReader, WebVTTReader, CaptionConverter
from shutil import copyfile

from myFunctions import (findSubFiles, runProcess,runProcessReturnOutput, 
                         prefEncoding)

def partFormat(searchPath, recursive, extension, keep, verbose):  # check subtitles encoding and format
    noFormat = 0
    srtFormat = 0
    samiFormat = 0
    dfxpFormat = 0
    kanal5Format = 0
    webvttFormat = 0
    dcsubFormat = 0
    wrongEncoding = 0
    wrongNumbering = 0
    # wrongFormat = 0
    emptyEntry = 0
    subFiles = []

    subFiles = findSubFiles(searchPath, recursive, extension, subFiles, False, verbose)
    
    if subFiles:
        for myFile in subFiles:
            print "\n%s" % myFile
            encoding = checkCoding(myFile, verbose)  # check encoding
            if encoding == prefEncoding:
                print "--- Encoded in %s" % encoding  # correct encoding
            else:
                print "*** Encoded in %s" % encoding  # wrong encoding
                changeEncoding(myFile, encoding, keep, verbose)  # set to preferred encoding
                wrongEncoding += 1

            myFormat = checkFormat(myFile, verbose)  # check format
            if verbose:
                print "--- Format: %s" % myFormat
            if not myFormat:
                print "*** Could not detect format"
                noFormat += 1
            elif myFormat == "srt":
                print "--- Srt format"
                srtFormat += 1
                if emptyEntries(myFile, keep, verbose):  # look for empty entries, if so delete them
                    emptyEntry += 1
                if numbering(myFile, keep, verbose):  # check if numbering is correct, if not correct it
                    wrongNumbering += 1
            elif myFormat == "sami":
                print "*** Sami format"
                samiFormat += 1
                samiToSrt(myFile, keep, verbose)  # convert from SAMI to SRT
                if emptyEntries(myFile, keep, verbose):  # check for empty entries, if so delete them
                    emptyEntry += 1
                if numbering(myFile, keep, verbose):  # check if numbering is correct, if not correct it
                    wrongNumbering += 1
            elif myFormat == "dfxp":
                print "*** Dfxp format"
                dfxpFormat += 1
                dfxpToSrt(myFile, keep, verbose)  # convert from DFXP to SRT
            elif myFormat == "kanal5":
                print "*** Kanal5 format"
                kanal5Format += 1
                kanal5ToSrt(myFile, keep, verbose)  # convert from KANAL5 to SRT
                if emptyEntries(myFile, keep, verbose):  # check for empty entries, if so delete them
                    emptyEntry += 1
                if numbering(myFile, keep, verbose):  # check if numbering is correct, if not correct it
                    wrongNumbering += 1
            elif myFormat == "webvtt":
                print "*** Webvtt format"
                webvttFormat += 1
                webvttToSrt(myFile, keep, verbose)  # convert from WEBVTT to SRT
            elif myFormat == "dcsub":
                print "*** DCSub format"
                dcsubFormat += 1
                dcsubToSrt(myFile, keep, verbose)  # convert from DCSUB to SRT
                
    if noFormat + srtFormat + samiFormat + kanal5Format + webvttFormat > 0:
        print "\nFormats:"
        if noFormat > 0:
            print "Not detected: %s" % noFormat
        if srtFormat > 0:
            print "srt: %s" % srtFormat
        if samiFormat > 0:
            print "sami: %s" % samiFormat
        if dfxpFormat > 0:
            print "dfxp: %s" % dfxpFormat
        if kanal5Format > 0:
            print "kanal5: %s" % kanal5Format
        if webvttFormat > 0:
            print "webvtt: %s" % webvttFormat
        if dcsubFormat > 0:
            print "dcsub: %s" % dcsubFormat 
        print

    if wrongEncoding > 0:
        print "Files with wrong encoding: %s" % wrongEncoding
        print

    if emptyEntry > 0:
        print "Files with empty entries: %s" % emptyEntry
        print

    if wrongNumbering > 0:
        print "File with wrong numbering: %s" % wrongNumbering
        print
        
def checkCoding(myFile, verbose):
    theFile = open(myFile)  # open sub
    soup = BeautifulSoup(theFile)  # read sub into BeautifulSoup
    theFile.close()  # close sub
    encoding = soup.originalEncoding  # let soup detect encoding
    if verbose:
        print "--- BeautifulSoup says: %s" % encoding
    if encoding == "ISO-8859-2":
        print "*** Detected ISO-8859-2. Assuming it's ISO-8859-1"
        encoding = "ISO-8859-1"
    elif encoding == "windows-1251":
        # print "*** Detected windows-1251. Assuming it's cp1251"
        # encoding = "cp1251"
        print "*** Detected windows-1251. Assuming it's ISO-8859-1"
        encoding = "ISO-8859-1"
    return encoding

def changeEncoding(myFile, encoding, keep, verbose):
    if verbose:
        print "--- Renaming to %s.%s" % (myFile, encoding)
    os.rename(myFile, "%s.%s" % (myFile, encoding))
    print "--- Changing encoding to %s" % prefEncoding
    blockSize = 1048576  # size in bytes to read every chunk
    with codecs.open("%s.%s" % (myFile, encoding), "r", encoding) as sourceFile:  # open the copy as source
        with codecs.open(myFile, "w", prefEncoding) as targetFile:  # open the target
            while True:
                contents = sourceFile.read(blockSize)
                if not contents:
                    break
                if verbose:
                    print "--- Writing %s" % myFile
                targetFile.write(contents)  # write chunk to target
    sourceFile.close()  # close source
    targetFile.close()  # close target
    if not keep:
        if verbose:
            print "--- Deleting temporary file %s.%s" % (myFile, encoding)
        os.remove("%s.%s" % (myFile, encoding))

def checkFormat(myFile, verbose):
    myFormat = ""
    
    if verbose:
        print "--- Checking subtitle format"
        
    capsFile = open(myFile)  # open sub
    caps = capsFile.read()  # read sub
    reader = detect_format(caps)  # detect format with pycaption
    
    if verbose:
        print "--- pycaption says: %s" % reader
        
    if reader:
        if "srt" in str(reader):
            myFormat = "srt"
        elif "sami" in str(reader):
            myFormat = "sami"
        elif "dfxp" in str(reader):
            myFormat = "dfxp"
        elif "webvtt" in str(reader):
            myFormat = "webvtt"    
    else:
        if verbose:
            print "*** pycaption could not detect format"
            print "--- Checking if it's DCSub..."
        DCSub = checkIfDCSub(myFile, verbose)
        if DCSub:
            if verbose:
                print "--- It probably is DCSub format"
            myFormat = "dcsub"
        else:
            if verbose:
                print "--- Checking if it's kanal5's own format..."
            if caps.startswith('[{"startMillis":'):
                if verbose:
                    print "--- It probably is kanal5 format"
                myFormat = "kanal5"
    
    capsFile.close()  # close sub
    
    return myFormat

def checkIfDCSub(myFile, verbose):
    DCSub = False
    
    if verbose:
        print "--- Extracting second line..."
    with open(myFile) as capsFile:
        for lineNo, line in enumerate(capsFile):
            if lineNo == 1:
                if verbose:
                    print "--- Second line reads: %s" % line.rstrip("\n")
                if "dcsub" in line.lower():
                    DCSub = True
                    #break
                
    return DCSub

def samiToSrt(myFile, keep, verbose):
    if verbose:
        print "--- Renaming to %s.sami" % myFile
    os.rename(myFile, "%s.sami" % myFile)
    print "--- Converting to srt"
    with codecs.open("%s.sami" % myFile, "r", encoding="utf8") as sourceFile:
        caps = sourceFile.read()  # read source                                               
    converter = CaptionConverter()  # set pycaptions converter                                
    converter.read(caps, SAMIReader())  # read sami                                           
    with codecs.open(myFile, "w", encoding="utf8") as targetFile:  # open target              
        targetFile.write(converter.write(SRTWriter()))  # write target                        
    sourceFile.close()  # close source                                                        
    targetFile.close()  # close target                                                        
    if not keep:
        if verbose:
            print "--- Deleting temporary file %s.sami" % myFile
        os.remove("%s.sami" % myFile)

def dfxpToSrt(myFile, keep, verbose):
    if verbose:
        print "--- Renaming to %s.dfxp" % myFile
    os.rename(myFile, "%s.dfxp" % myFile)
    print "--- Converting to srt"
    sourceFile = open("%s.dfxp" % myFile)  # open copy as source
    caps = sourceFile.read()  # read source
    converter = CaptionConverter()  # set pycaptions converter
    converter.read(caps, DFXPReader())  # read sami
    with open(myFile, "w") as targetFile:  # open target
        targetFile.write(converter.write(SRTWriter()))  # write target
    sourceFile.close()  # close source
    targetFile.close()  # close target
    if not keep:
        if verbose:
            print "--- Deleting temporary file %s.dfxp" % myFile
        os.remove("%s.dfxp" % myFile)
        
def webvttToSrt(myFile, keep, verbose):
    if verbose:
        print "--- Renaming to %s.webvtt" % myFile
    os.rename(myFile, "%s.webvtt" % myFile)
    print "--- Converting to srt"
    sourceFile = codecs.open("%s.webvtt" % myFile, "r", encoding="utf8")  # open copy as source
    caps = sourceFile.read()  # read source
    converter = CaptionConverter()  # set pycaptions converter
    converter.read(caps, WebVTTReader())  # read sami
    with codecs.open(myFile, "w", encoding="utf8") as targetFile:  # open target
        targetFile.write(converter.write(SRTWriter()))  # write target
    sourceFile.close()  # close source
    targetFile.close()  # close target
    if not keep:
        if verbose:
            print "--- Deleting temporary file %s.webvtt" % myFile
        os.remove("%s.webvtt" % myFile)
        
def kanal5ToSrt(myFile, keep, verbose):
    import datetime
    
    lineNo = 1
    
    if verbose:
        print "--- Renaming to %s.kanal5" % myFile
    os.rename(myFile, "%s.kanal5" % myFile)
    print "--- Converting to srt"
    
    sourceFile = open("%s.kanal5" % myFile, 'r')
    targetFile = open(myFile, 'w')
    caps = eval(sourceFile.read())

    for line in caps:
        start = str(datetime.timedelta(milliseconds=line['startMillis'])).replace('.', ',')
        stop = str(datetime.timedelta(milliseconds=line['endMillis'])).replace('.', ',')
        targetFile.write("%d\n " % lineNo)
        targetFile.write("%s --> %s\n" % (start, stop))
        targetFile.write(line['text'])
        targetFile.write("\n\n")
        lineNo += 1
    targetFile.close()
    sourceFile.close()
    
    if not keep:
        if verbose:
            print "--- Deleting temporary file %s.kanal5" % myFile
        os.remove("%s.kanal5" % myFile)    
        
def dcsubToSrt(myFile, keep, verbose):
    if verbose:
        print "--- Renaming to %s.dcsub" % myFile
    os.rename(myFile, "%s.dcsub" % myFile)
    print "--- Converting to srt"
    cmd = 'dcsubtitle_to_srt.py "%s"' % ("%s.dcsub" % myFile)
    output = runProcessReturnOutput(cmd, verbose)
    with open(myFile, "w") as targetFile:  # open target
        targetFile.write(output[0])
    targetFile.close()  # close target

    
    
    if not keep:
        if verbose:
            print "--- Deleting temporary file %s.dcsub" % myFile
        os.remove("%s.dcsub" % myFile)

def emptyEntries(myFile, keep, verbose):
    emptyEntryFound = False
    emptyEntries = 0
    entriesToDelete = []

    if verbose:
        print "--- Searching for empty entries"
    subs = pysrt.open(myFile, encoding='utf-8')  # open sub with pysrt as utf-8
    entries = len(subs)  # count entries
    if verbose:
        print "--- %s entries total" % entries

    for entryNo in range(0, entries):  # count entry numbers up to number of entries
        subEntry = u"%s" % subs[entryNo]  # read single entry
        lines = subEntry.split('\n')  # split entry into lines
        lineNo = 0  # set first line to 0
        emptyEntry = False

        for row in lines:  # read lines one by one
            if lineNo == 2:
                if (row == "&nbsp;" 
                    or row == "&nbsp" 
                    or not row):  # if third line is &nbsp; or empty
                    emptyEntry = True
            if emptyEntry and lineNo == 3 and row == "":  # if third line is &nbsp; and fourth line is empty
                emptyEntryFound = True
                emptyEntries += 1
                entriesToDelete.append(entryNo)  # add entry number to list
            lineNo += 1

    if emptyEntryFound:  # if empty entry is found
        print "*** %s empty entries found" % emptyEntries

        for entryNo in reversed(entriesToDelete):  # run through entry numbers in reverse
            # print lineNo
            del subs[entryNo]  # delete entry
            
        if keep:
            if verbose:
                print "--- Copying original file to %s.emptyEntries" % myFile
            copyfile(myFile, "%s.emptyEntries" % myFile)
            
        subs.save(myFile, encoding='utf-8')  # save sub

        subs = pysrt.open(myFile, encoding='utf-8')  # open new sub with pysrt
        entries = len(subs)  # count entries
        print "--- Now has %s entries" % entries
        
    return emptyEntryFound

def numbering(myFile, keep, verbose):
    wrongNumbering = False

    if verbose:
        print "--- Checking numbering"

    subs = pysrt.open(myFile, encoding='utf-8')  # open sub with pysrt as utf-8
    entries = len(subs)  # count entries

    for entryNo in range(0, entries):  # count entry numbers up to number of entries
        subEntry = u"%s" % subs[entryNo]  # read single entry
        lines = subEntry.split('\n')  # split entry into lines
        if entryNo + 1 != int(lines[0]):  # entry number does not match real numbering
            wrongNumbering = True
            print "*** Correcting numbering"
            copyfile(myFile, "%s.wrongNumbering" % myFile)
            break

    if wrongNumbering:
        targetFile = codecs.open(myFile, "w", prefEncoding)
        subs = pysrt.open("%s.wrongNumbering" % myFile, encoding='utf-8')  # open sub with pysrt as utf-8
        entries = len(subs)  # count entries
        for entryNo in range(0, entries):  # count entry numbers up to number of entries
            subEntry = u"%s" % subs[entryNo]  # read single entry
            lines = subEntry.split('\n')  # split entry into lines
            noLines = len(lines)  # number of lines in each entry
            for line in range(0, noLines):
                if line == 0:
                    targetFile.write("%s\n" % str(entryNo + 1))
                    # print entryNo + 1
                else:
                    targetFile.write("%s\n" % lines[line])
                    # print lines[line]
        targetFile.close()

        if not keep:
            if verbose:
                print "--- Deleting %s.wrongNumbering" % myFile
            os.remove("%s.wrongNumbering" % myFile)

    return wrongNumbering
