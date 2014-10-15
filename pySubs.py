#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

# edit .conf to suit your needs

import getopt

from myFunctions import * 
from link import partLink
from status import partStatus
from get import partGet
from check import partCheck
from format import partFormat
from rename import partRename

##### handle arguments #####
try:
    myopts, args = getopt.getopt(sys.argv[1:],'p:re:ldgc:fn:skhv' ,
                                 ['path=', 'recursive', 'extension=',
                                  'link', 'detectlang', 'get',
                                  'check=', 'format', 'rename=', 'search',
                                  'keep', 'help', 'verbose'])

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
doRename = False
renameVideo = False
renameSub = False
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

if not doLink and not doStatus and not doGet and not doCheck and not doFormat and not doRename: # no program part selected
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



########################################## choose what to run ##########################################
if doLink and not doStatus and not doGet and not doCheck and not doFormat and not doRename: # find language in subs and create links
    partLink(recursive, searchPath, extension, verbose)

elif doStatus and not doLink and not doGet and not doCheck and not doFormat  and not doRename: # status at detectlanguage.com
    partStatus(verbose)

elif doGet and not doLink and not doStatus and not doCheck and not doFormat and not doRename: # get subs for video files
    partGet(searchPath, recursive, verbose)

elif doFormat and not doLink and not doGet and not doCheck and not doStatus and not doRename: # check subs format, convert to UTF-8 and convert to srt
    partFormat(searchPath, recursive, extension, findCode, keep, verbose)

elif doLink and doGet and not doStatus and not doFormat and not doRename: # get and link
    partGet(searchPath, recursive, verbose)
    print "----------------------------------------------------------------"
    partLink(recursive, searchPath, extension, verbose)

elif doFormat and doLink and not doGet and not doStatus and not doCheck and not doRename: # format and link
    partFormat(searchPath, recursive, extension, findCode, keep, verbose)
    print "----------------------------------------------------------------"
    partLink(recursive, searchPath, extension, verbose)

elif doCheck and not doLink and not doGet and not doStatus and not doFormat and not doRename: # check language codes manually
    partCheck(recursive, searchPath, extension, findCode, verbose)
    
elif doRename and not doLink and not doStatus and not doGet and not doCheck and not doFormat: # rename video files with data from thetvdb api
    partRename(searchPath, recursive, extension, renameVideo, renameSub, verbose)

else:
    onError(5, 5)
