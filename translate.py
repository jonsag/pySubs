#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import os, codecs, re, sys, urllib.request, urllib.error, urllib.parse

import xml.etree.ElementTree as ET

from myFunctions import (findSubFiles, hasLangCode, checkLang, continueWithProcess, 
                         langName, 
                         prefLangs, prefEncoding, maxTrys, 
                         msClientID, msClientSecret, 
                         yandexTranslateXML)

from format import checkCoding, checkFormat

import goslate, msmt
gs = goslate.Goslate()

from mstranslate import MSTranslate

def partTranslate(recursive, searchPath, extension, translateEngine, checkCode, verbose):
    #langSums = []
    #subsFound = []
    #num = 0
    subFiles = []
    #ask = False
    
    # gs = goslate.Goslate()
    # print gs.translate('hello world', 'sv')
    # sys.exit()
    
    print("--- Will try to translate into %s" % langName(prefLangs[0]).lower())
    
    # print sys.getdefaultencoding()
    
    # print "%s%s" % (yandexGetLangsXML, prefLangs[0])
    # print "%s%s" % (yandexGetLangsJSON, prefLangs[0])
    
    # sampleText = "Hello world!"
    # sampleText = sampleText.replace(" ", "+")
    # print "%s%s" % (yandexDetectXML, sampleText)
    # print "%s%s" % (yandexDetectJSON, sampleText)
    
    # fromLang = "en"
    # toLang = prefLangs[0]
    # print "%s%s%s" % (yandexTranslateXML, ("%s-%s" % (fromLang, toLang)), "&text=%s" % sampleText)
    # print "%s%s%s" % (yandexTranslateJSON, ("%s-%s" % (fromLang, toLang)), "&text=%s" % sampleText)
    
    # sys.exit()

    subFiles = findSubFiles(searchPath, recursive, extension, subFiles, checkCode, verbose)

    if subFiles: 
        for myFile in subFiles:
            print("\n%s" % myFile)
            
            if (checkCoding(os.path.join(searchPath, myFile), verbose) == prefEncoding):  # or
                # checkCoding(os.path.join(searchPath, myFile), verbose) == "ascii"):
                codingOK = True
            else:
                codingOK = False
            
            if codingOK and checkFormat(os.path.join(searchPath, myFile), verbose) == "srt":
                print("--- Correct coding and format")
                existingCode = hasLangCode(os.path.join(searchPath, myFile))
                if existingCode['code'] == prefLangs[0]:
                    print("--- Already has langcode %s" % prefLangs[0])
                    existingLanguage = checkLang(os.path.join(searchPath, myFile), verbose)
                    if existingLanguage == prefLangs[0]:
                        print("--- detectlanguage.com agrees")
                    else:
                        print("*** detectlanguage.com does not agree")
                        translate(os.path.join(searchPath, myFile), existingLanguage, prefLangs[0], translateEngine, verbose)
                else:
                    translate(os.path.join(searchPath, myFile), existingCode['code'], prefLangs[0], translateEngine, verbose)
            else:
                print("*** Incorrect coding or format")
                
def translate(myFile, fromLanguage, toLanguage, translateEngine, verbose):
    textLines = []
    newLines = []
    outLines = []
    stage = ""
    lineNo = 0

    print("--- Trying to translate from %s to %s using %s..." % (langName(fromLanguage).lower(),
                                                                 langName(toLanguage).lower(),
                                                                 translateEngine))
    if translateEngine == "msmt":
        if verbose:
            print("--- Generating token...")
        msToken = msmt.get_access_token(msClientID, msClientSecret)
        
    if translateEngine == "ms":
        if verbose:
            print("--- Generating token...")
        msT = MSTranslate(msClientID, msClientSecret)
    
    with codecs.open(myFile, encoding=prefEncoding) as inFile:  # open file
        inLines = inFile.read().splitlines()
    inFile.close()  # close file
    
    for inLine in inLines:
        if len(textLines) > 0 and inLine == "":
            for textLine in textLines:
                if verbose:
                    print("old - %s" % textLine)
            if verbose:
                if lineNo == 1:
                    countWord = "line"
                else:
                    countWord = "lines"
                print("--- Sending %d %s to %s..." % (lineNo, countWord, translateEngine))
               
            if translateEngine == "yandex":
                newLines = yandexXMLTranslate(textLines, fromLanguage, toLanguage, verbose)
            elif translateEngine == "goslate":
                newLines = goslateTranslate(textLines, fromLanguage, toLanguage, verbose)
            elif translateEngine == "msmt":
                newLines = msmtTranslate(textLines, fromLanguage, toLanguage, msToken, verbose)
            elif translateEngine == "ms":
                newLines = msTranslate(textLines, fromLanguage, toLanguage, msT, verbose)
            elif translateEngine == "test":
                newLines = []
                for textLine in textLines:
                    textLine = [x for x in textLine if x in string.printable]
                    newLines.append(textLine)
            else:
                sys.exit()
                
            for newLine in newLines:
                if verbose:
                    print("new - %s" % newLine)
                outLines.append(newLine)
                
            lineNo = 0
            textLines = []
        
        if inLine == "":
            if verbose:
                print()
            outLines.append(inLine)
            stage = "linefeed"
        elif inLine.isdigit():
            if verbose:
                print("num - %s" % inLine)
            outLines.append(inLine)
            if stage == "linefeed":
                stage == "numbering"
        elif re.match("^[0-9:',.>'\- \]]*$", inLine):
            if verbose:
                print("tc  - %s" % inLine)
            outLines.append(inLine)
            if stage == "numbering":
                stage = "timecode"
        else:
            textLines.append(inLine)
            stage = "text"
            lineNo += 1        
    
    newName = newFileName(myFile, translateEngine, toLanguage, verbose)

    if continueWithProcess(newName, True, False, verbose):        
        targetFile = codecs.open(newName, "w", prefEncoding)
        if verbose:
            print("--- Writing to %s" % newName)
        for outLine in outLines:
            if verbose:
                print(outLine)
            targetFile.write("%s\n" % outLine)
        
        targetFile.close()
        
def newFileName(myFile, translateEngine, toLanguage, verbose):
    if verbose:
        print("--- Old file name: %s" % myFile)
    extension = os.path.splitext(myFile)[1]
    newName = os.path.splitext(myFile)[0]
    if hasLangCode(myFile):
        newName = os.path.splitext(newName)[0]
    newName = "%s.%s.%s%s" % (newName, translateEngine, toLanguage, extension)
    if verbose:
        print("--- New file name: %s" % newName)
        
    return newName
    
def yandexXMLTranslate(inLines, fromLanguage, toLanguage, verbose):
    outLines = []
    #trys = 0
    lineNo = 0
    
    for inLine in inLines:
        if lineNo == 0:
            inText = inLine
        else:
            inText = "%s&text=%s" % (inText, inLine)
        lineNo += 1
            
    lineNo = 0            
    
    inText = inText.strip("#").lstrip(" ").rstrip(" ").replace(" ", "+")
    inText = [x for x in inText if x in string.printable]
    
    if verbose:
        print("--- inText - %s" % inText)
        
    requestUrl = "%s%s%s" % (yandexTranslateXML, ("%s-%s" % (fromLanguage, toLanguage)), "&text=%s" % inText)
    if verbose:
        print("--- URL: %s" % requestUrl)

    yandexXML = urllib.request.urlopen(requestUrl).read()
    if verbose:
        print("--- Response:\n%s" % yandexXML)
    xmlRoot = ET.fromstring(yandexXML)  # read xml
    
    for xmlChild in xmlRoot:

        if xmlRoot.attrib['code'] == "200" and 'text' in xmlChild.tag:
            outLines.append(xmlChild.text)
        else:
            outLines.append("*** Could not translate ***")

    if verbose:
        for outLine in outLines:
            print("--- outText: %s" % outLine)
    
    return outLines

def goslateTranslate(inLines, fromLanguage, toLanguage, verbose):
    outLines = []
    
    for inLine in inLines:
        trys = 0
        inLine = inLine.strip("#").lstrip(" ").rstrip(" ") 
        if verbose:
            print("--- inText - %s" % inLine)
        # outLine = gs.translate(inLine, toLanguage)
        # outLines.append(outLine)
        while True:
            trys += 1
            if trys > maxTrys:
                print("*** Tried %s times\n    Giving up...")
                outLines.append("*** Could not translate ***")
                break
            try:
                outLine = gs.translate(inLine, toLanguage)
            except:
                print(sys.exc_info()[0]) 
                print("*** Something went wrong\n    Trying again")
            else:
                outLines.append(outLine)
                break         
        
    if verbose:
        for outLine in outLines:
            print("--- outText: %s" % outLine)
    
    return outLines

def msmtTranslate(inLines, fromLanguage, toLanguage, msToken, verbose):
    outLines = []
    
    for inLine in inLines:
        inLine = inLine.strip("#").lstrip(" ").rstrip(" ")  # .replace(" ", "+")
        if verbose:
            print("--- inText - %s" % inLine)
        response = msmt.translate(msToken, inLine, toLanguage, fromLanguage)
        outLines.append(response)
        
    if verbose:
        for outLine in outLines:
            print("--- outText: %s" % outLine)
            
    sys.exit()
        
    return outLines
        
def msTranslate(inLines, fromLanguage, toLanguage, msT, verbose):    
    outLines = []
    
    for inLine in inLines:
        inLine = inLine.strip("#").lstrip(" ").rstrip(" ")  # .replace(" ", "+")
        # inLine = filter(lambda x: x in string.printable, inLine)
        if verbose:
            print("--- inText - %s" % inLine)
        response = msT.translate(inLine, toLanguage, fromLanguage)
        outLines.append(response)
        
    if verbose:
        for outLine in outLines:
            print("--- outText: %s" % outLine)
        
    return outLines


