#!/usr/bin/env python
# -*- coding: utf-8 -*-

lines = 10

import sys, getopt
import detectlanguage

detectlanguage.configuration.api_key = "3e914ec272f0dfca6a7d8237e1cbd604"

# parse arguments
print 'Number of arguments:', len(sys.argv), 'arguments.'
print 'Argument List:', str(sys.argv), '\n'

script = sys.argv[0]


ifile = ''
ofile = ''
text = ''
 
###############################
# o == option
# a == argument passed to the o
###############################
# Cache an error with try..except 
# Note: options is the string of option letters that the script wants to recognize, with 
# options that require an argument followed by a colon (':') i.e. -i fileName
#
try:
    myopts, args = getopt.getopt(sys.argv[1:],"t:i:o:")
except getopt.GetoptError as e:
    print (str(e))
    print '\nUsage:'
    print '%s -i input -o output' % script
    print 'OR'
    print '%s -t text'
    sys.exit(2)
 
for o, a in myopts:
    if o == '-i':
        ifile = a
    elif o == '-o':
        ofile = a
    elif o == '-t':
        text = a
 
# Display input and output file name passed as the args
if ifile and not text:
    print 'Input file: %s' % ifile
    print 'Output file: %s' % ofile
elif text and not ifile:
    print 'Input text: %s' % text
else:
    print 'Incompatible arguments given. Exiting...'
    sys.exit(3)



if ifile and not text:
    print '\nInfile has %d lines' % sum(1 for line in open(ifile))
    intext = open(ifile)
    with open(ifile) as myfile:
       head = myfile.readlines(6)
    text = str(head)
#    text = intext.read()
    print '\nFirst %d lines in %s:' % (lines,ifile)
    print text

if not text:
   print 'No text given. Exiting...'
   sys.exit(y)


# detect
result = detectlanguage.detect(text)
#print result

print '\nLanguagecode is: %r' % str(result[0]['language'])

if result[0]['isReliable']:
    print 'Answer is reliable'
else:
    print 'Answer is NOT reliable'

print 'Confidence is: %d' % result[0]['confidence']

# account status
status = detectlanguage.user_status()
#print status

print '\nRequest: %d / %d' % (status['requests'], status['daily_requests_limit'])
print 'Bytes: %d / %d' % (status['bytes'], status['daily_bytes_limit'])
