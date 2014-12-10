#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

# edit .conf to suit your needs

import getopt

# import sys, os

# from myFunctions import onError, usage, languages
from myFunctions import *

##### handle arguments #####
try:
    myopts, args = getopt.getopt(sys.argv[1:], 'p:re:ldg:c:ft:n:skhv' ,
                                 ['path=', 'recursive', 'extension=',
                                  'link', 'detectlang', 'get=',
                                  'check=', 'format', 'translate=',
                                  'rename=', 'search',
                                  'keep', 'help', 'verbose'])

except getopt.GetoptError as e:
    onError(1, str(e))

recursive = False
extension = ".srt"
searchPath = os.path.abspath(os.getcwd())
doLink = False
doStatus = False
getSubs = ""
checkCode = ""
doFormat = False
doTranslate = ""
doRename = False
renameVideo = False
renameSub = False
verbose = False
keep = False

if len(sys.argv) == 1:  # no options passed
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
        if argument == "all" or argument == "pref":
            getSubs = argument
        else:
            for language in languages:
                if argument == language['code']:
                    getSubs = argument
        if not getSubs:
            onError(6, argument)
    elif option in ('-h', '--help'):
        usage(0)
    elif option in ('-c', '--check'):
        if argument == "all" or argument == "pref" or argument == "force":
            checkCode = argument
        else:
            for language in languages:
                if argument == language['code']:
                    checkCode = argument
        if not checkCode:
            onError(6, argument)
    elif option in ('-f', '--format'):
        doFormat = True
    elif option in ('-t', '--translate'):
        for translateEngine in translateEngines:
            if argument == translateEngine:
                doTranslate = argument
        if not doTranslate:
            onError(8, "Not a valid argument to -t (--translate)")
    elif option in ('-n', '--rename'):
        doRename = True
        if argument == "all":
            renameVideo = True
            renameSub = True
        elif argument in "videos":
            renameVideo = True
        elif argument in "subs":
            renameSub = True
        else:
            onError(7, argument)
    elif option in ('-k', '--keep'):
        keep = True
    elif option in ('-v', '--verbose'):
        verbose = True

if not doLink and not doStatus and not getSubs and not checkCode and not doFormat and not doRename and not doTranslate:  # no program part selected
    onError(3, 3)

if searchPath:  # argument -p --path passed
    if not os.path.isdir(searchPath):  # not a valid path
        onError(4, searchPath)
else:
    print "\nNo path given."
    print "Using current dir %s" % searchPath

if extension:  # argument -e --extension passed
    extension = ".%s" % extension.lstrip('.')  # remove leading . if any
else:
    print "\nNo extension given!"
    print "Setting %s" % extension.lstrip('.')  # remove leading . if any



########################################## choose what to run ##########################################
if doLink and not doStatus and not getSubs and not checkCode and not doFormat and not doRename and not doTranslate:  # find language in subs and create links
    from link import partLink
    partLink(recursive, searchPath, extension, verbose)

elif doStatus and not doLink and not getSubs and not checkCode and not doFormat  and not doRename and not doTranslate:  # status at detectlanguage.com
    from status import partStatus
    partStatus(verbose)

elif getSubs and not doLink and not doStatus and not checkCode and not doFormat and not doRename and not doTranslate:  # get subs for video files
    from get import partGet
    partGet(searchPath, recursive, getSubs, verbose)

elif doFormat and not doLink and not getSubs and not checkCode and not doStatus and not doRename and not doTranslate:  # check subs format, convert to UTF-8 and convert to srt
    from format import partFormat
    partFormat(searchPath, recursive, extension, keep, verbose)

elif doLink and getSubs and not doStatus and not doFormat and not doRename and not doTranslate:  # get and link
    from link import partLink
    from get import partGet
    partGet(searchPath, recursive, getSubs, verbose)
    print "----------------------------------------------------------------"
    partLink(recursive, searchPath, extension, verbose)

elif doFormat and doLink and not getSubs and not doStatus and not checkCode and not doRename and not doTranslate:  # format and link
    from link import partLink
    from format import partFormat
    partFormat(searchPath, recursive, extension, keep, verbose)
    print "----------------------------------------------------------------"
    partLink(recursive, searchPath, extension, verbose)

elif checkCode and not doLink and not getSubs and not doStatus and not doFormat and not doRename and not doTranslate:  # check language codes manually
    from check import partCheck
    partCheck(recursive, searchPath, extension, checkCode, verbose)
    
elif doRename and not doLink and not doStatus and not getSubs and not checkCode and not doFormat and not doTranslate:  # rename video files with data from thetvdb api
    from rename import partRename
    partRename(searchPath, recursive, extension, renameVideo, renameSub, verbose)
    
elif doTranslate and not doLink and not doStatus and not getSubs and not checkCode and not doFormat and not doRename:  # translate subtitles
    from translate import partTranslate
    partTranslate(recursive, searchPath, extension, doTranslate, checkCode, verbose)
    
else:
    onError(5, 5)
