#!/usr/bin/env python

import detectlanguage
detectlanguage.configuration.api_key = "3e914ec272f0dfca6a7d8237e1cbd604"

##### show available languages #####

languages = detectlanguage.languages()

numberLanguages = len(languages)

print "%d available languages" % numberLanguages
print "%s %s" % (languages[0], languages[1])
print "-------------------------------------------------------------------------------------"

for language in range(0, numberLanguages):

    if language >= numberLanguages:
        break

    print "%s %s" %(languages[language]['code'], languages[language]['name'])

print "\n%d available languages" % numberLanguages

##### account status #####

status = detectlanguage.user_status()

print "\ndetectlanguage.com status for API-key: %s" % detectlanguage.configuration.api_key
print "-------------------------------------------------------------------------------------"
print "Status: %s" %status['status']
print "Account type/plan: %s" % status['plan']
print "\nTodays date: %s" % status['date']
print "Plan expires: %s" % status['plan_expires']
print '\nRequest: %d / %d' % (status['requests'], status['daily_requests_limit'])
print 'Bytes: %d / %d' % (status['bytes'], status['daily_bytes_limit'])
