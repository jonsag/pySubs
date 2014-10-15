#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from myFunctions import *

def partStatus(verbose): # check accounts status at detectlanguage.com
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