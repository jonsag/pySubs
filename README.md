Tools to help with naming of subtitle files, and downloading subtitles.

Requirements:
----------------------------------------------
  Python modules:  
  	* babelfish,		python-babelfish  
  	* detectlanguage,						pip install detectlanguage  
  	* goslate,  
  	* msmt,  
    * mstranslate,							pip install mstranslate  
    * pysrt,  
    * pycaption,							pip install pycaption  
    * subliminal,		python-subliminal,	pip install --upgrade subliminal  
    
Register account at detectlanguage,com:
----------------------------------------------    
Visit detectlanguage.com  
Enter your new API-key in config.ini  
The one already in config will not work  

Install dc subtitle module
----------------------------------------------
Download 'dcsubtitle_to_srt.py'  
from http://codegists.com/snippet/python/dcsubtitle_to_srtpy_naglis_python  
or https://gist.github.com/naglis/ee95a03d8f84d36fe2c3  
or copy and paste this to said file,  
put it in your PATH and make it executable:  
	
	#!/usr/bin/env python3  
	# -*- coding: utf-8 -*-  
	# Encoding: UTF-8  
	
	import os  
	import argparse  
	import xml.etree.ElementTree as ET  
	 
	"""  
	Converts DLP Cinema™ XML (DCSubitle) subtitles to SubRip (.srt)  
	 
	Tested with Python 3.4  
	 
	Specification:  
	    http://www.dlp.com/downloads/pdf_dlp_cinema_CineCanvas_Rev_C.pdf  
	"""  
	 
	 
	def dc_time_to_srt_time(dc_time):  
	    """Returns a time representation suitable for SubRip format.  
	 
	    Return format: hh:mm:ss,ms  
	    """  
	    return '{0:}:{1:}:{2:},{3:}'.format(*dc_time.split(':'))  
	 
	 
	def parse_dc_subtitles(xml):  
	    """Returns a list of dicts with parsed subtitles."""  
	    subs = {}  
	    root = ET.fromstring(xml)  
	    font = root.find('Font')  
	    for sub in font.findall('Subtitle'):  
	        attrs = sub.attrib  
	        number = int(attrs['SpotNumber'])  
	        start, end = attrs['TimeIn'], attrs['TimeOut']  
	        subs[number] = {  
	            'text': '\n'.join([text.text for text in sub.findall('Text')]),  
	            'start': start,  
	            'end': end,  
	        }  
	    return subs  
	 
	 
	def main():  
	    p = argparse.ArgumentParser()  
	    p.add_argument('filename', help='path to the XML file')  
	    p.add_argument('--encoding', help='encoding of the XML file')  
	    args = p.parse_args()  
	 
	    filename = os.path.expanduser(args.filename)  
	 
	    with open(filename, encoding=args.encoding) as f:  
	        xml = f.read()  
	 
	    subs = parse_dc_subtitles(xml)  
	 
	    for nr in sorted(subs):  
	        s = subs[nr]  
	        print(nr)  
	        print(  
	            dc_time_to_srt_time(s['start']),  
	            '-->',  
	            dc_time_to_srt_time(s['end'])  
	        )  
	        print(s['text'], end='\n\n')  
	 
	 
	if __name__ == '__main__':  
	    main()  

    
Usage:  
-----------------------------------------------

-l  
Check what language subtitle is  
Add language code before file extension  
Create link to subtitle  

-g  
Try to download subtitle  

-f  
Check and correct formatting  

-c  
Check if the language code is correct  

-d  
Check the status for your account at detectlanguage.com  

-h  
Print help text  
