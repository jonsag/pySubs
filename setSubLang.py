#!/usr/bin/env python
# -*- coding: utf-8 -*-

# edit .conf to suit your needs

# options:
# -p <path> scan single path
# -r <path> scan path recursively
# -s <suffix> file suffix to search for

import sys, getopt, os

from myFunctions import *

##### set config file #####
#config = configparser.ConfigParser()
#config.sections()
#config.read('setSubLang.ini') # read config file

##### handle arguments #####
try:
    myopts, args = getopt.getopt(sys.argv[1:],"p:r:s:")
except getopt.GetoptError as e:
    print (str(e))
    print '\nUsage:'
    print '%s -p <path> -s <suffix>' % sys.argv[0]
    print 'OR'
    print '%s -r <path> -s <suffix>' % sys.argv[0]
    sys.exit(2)

for o, a in myopts:
    if o == '-p':
        searchPath = a
    elif o == '-r':
        searchPathRecursive = a
    elif o == '-s':
        suffix = a

# check that a path is given
if not searchPathRecursive and not searchPath:
    print "\nError: No search path given!"
    print '\nUsage:'
    print '%s -p <path> -s <suffix>' % sys.argv[0]
    print 'OR'
    print '%s -r <path> -s <suffix>' % sys.argv[0]
    sys.exit(3)

# check that only one path is given
if searchPathRecursive and searchPath:
    print "\nError: You can't state both path and recursive path!"
    print '\nUsage:'
    print '%s -p <path> -s <suffix>' % sys.argv[0] 
    print 'OR'
    print '%s -r <path> -s <suffix>' % sys.argv[0]
    sys.exit(4)

# check if suffix is given
if not suffix:
    print "\nError: No suffix given!"
    print '\nUsage:'
    print '%s -p <path> -s <suffix>' % sys.argv[0] 
    print 'OR'
    print '%s -r <path> -s <suffix>'
    sys.exit(5)

# check that path exist
if searchPathRecursive:
    if not os.path.isdir(searchPathRecursive):
        print "\nError: %s is not a valid path!" % searchPathRecursive
        sys.exit(6)
    else:
        searchPath = searchPathRecursive
        recursive = " recursively"
else:
    if not os.path.isdir(searchPath):
        print "\nError: %s is not a valid path!" % searchPath
        sys.exit(6)
    else:
        recursive = ""

suffix = ".%s" % suffix

print "\nSearching %s%s for files ending with %s" % (searchPath, recursive, suffix)

# scan directories recursively
if searchPathRecursive:
    for root, dirs, files in os.walk(searchPath):
        for file in files:
            if isFile(os.path.join(root, file), suffix):
                langSums = fileFound(os.path.join(root, file), langSums)
                num += 1

# scan single directory
if searchPath:
    for file in os.listdir(searchPath):
        if isFile(file, suffix):
            langSums = fileFound(file, langSums)
            num += 1

print "\nNumber of %s files in %s: %d\n" % (suffix, searchPath, num)

print "Languages found:"
for lang in languages:
    langSum = langSums.count(lang['code'])
    if langSums.count(lang['code']) > 0:
        print "%s - %s:  %d" % (lang['code'], lang['name'].lower(), langSum)
print "\n"
