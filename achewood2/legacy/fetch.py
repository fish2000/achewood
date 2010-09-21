#!/usr/bin/env python
# encoding: utf-8
from __future__ import with_statement

"""
fetch.py

Created by Christian Swinehart on 2007-08-17.
Tweaked slightly by FI$H 2000 almost exactly three years later, coincedentally.
Copyright (c) 2007, 2010 Samizdat Drafting Co. All rights reserved.
"""

"""
import eventlet
urllib2 = eventlet.import_patched('urllib2')
eventlet.monkey_patch()

unionpool = eventlet.GreenPool(10)
"""


try:
	import re2 as re
except ImportError:
	import re
	print "Using standard library regexes"
else:
	print "Using Google RE2 regexes (fallback to standard library)"
	re.set_fallback_notification(re.FALLBACK_WARNING)


import sys, os, shutil, types, time, urllib2
from Cheetah.Template import Template
from glob import glob
from model import *
from sqlobject.dberrors import DuplicateEntryError
from BeautifulSoup import BeautifulSoup

defaultencoding = 'iso-8859-1'
#defaultencoding = 'utf-8'
prefix = "http://m.assetbar.com/achewood/"

# added the explicit match for question marks to keep the urlopen() in process_monthly() from 404ing
# maybe the fine men and women at 'asset bar' changed their url scheme?
# anyway all the urlopen()s got slapped unthinkingly into clunky try/excepts (see below) as part of my quest for this knowledge --fish
#monthly_re = re.compile(r"archive\?start=\d\d\d\d\d\d\d\d")
monthly_re = re.compile(r"archive\?start=2010\d\d\d\d")



def main():
	fetch()
	generatePages()

def fetch():
	main_index=prefix+"archive"
	
	# even if your code is totally turned to crud to the point where a crab on the beach has it as a big hot meal instead of a dead tern nearby
	# non-geeks will still be impressed and compare it to "the matrix" if it prints out enough stuff on the screen when it runs
	print "Doing a thing: %s" % main_index
	
	try:
		pageText = urllib2.urlopen(main_index).read()
	except urllib2.HTTPError, erm:
		print "fetch(): HTTP FAIL: url %s" % main_index
		print "fetch(): HTTP FAIL: error %s" % erm
		sys.exit(2)
	
	# I get the logic that was here but reassigning temp vars with listcomps as this bit did originally is something that riles up my obsessive compulsions
	# I am sorry to have stylistically edited your code dogg but I could not control myself
	# the only other other thing that had to be done by me was converting spaces to tabs
	# I sent you one of our "I'm Sorry I Use Different Code-Indenting Settings Than Other People" dude-to-dude greeting cards in today's mail
	# on the inside it says "For Me It's Tabs And I Respect Your Personal Choice As Long As You Don't Explain It In Such A Way That Girls Could Hear Us Talking" --fish
	index_pages = [prefix+url for url in monthly_re.findall(pageText)]
	month_hash = {}
	#unionpile = eventlet.GreenPile(unionpool)
	
	if not os.path.exists('comics/img'):
		os.makedirs('comics/img')
	
	print ""
	print "About to retrieve %s month URLs up ins..." % len(index_pages)
	print ""
	
	
	for month_url in index_pages:
		print "Fetching from %s" % month_url
		month_text = urllib2.urlopen(month_url).read()
		process_month(month_url, month_text)
	
	""" eventlet nonsense follows.
	for month_url in index_pages:
		print "Fetching from %s" % month_url
		unionpile.spawn(lambda u: (u, urllib2.urlopen(u).read()), month_url)
	
	for month_url, month_text in unionpile:
		print "\nGetting all comics from %s" % month_url
	"""



def repairEntities(brokenText):
	fixedText = brokenText
	replacements = [(r'&Atilde;&reg;','&icirc;'),
					(r'&Atilde;&copy;','&eacute;'),
					(r'&acirc;&euro;&trade;','&rsquo;'),
					(r'&#147;','&lsquo;'),
					(r'&#148;','&rsquo;'),
					(r'&Acirc;&cent;','&cent;'),
					(r'&Acirc;&rsquo;','&rsquo;'),
					(r' & ',' &amp; ')
	]
	
	for subSearch, subReplace in replacements:
		fixedText = re.subn(subSearch, subReplace, fixedText)[0]
	return unicode(fixedText, 'utf-8')

tmpl = open('template.html').read()
def generatePages():
	allComics = Comic.select(orderBy="uid")
	print "[DB] got", allComics.count(), "files"
	
	for i in xrange(allComics.count()):
		thisComic = allComics[i]
		print "Processing HTML for", thisComic.uid
		
		if i < allComics.count() - 1:
			tomorrowLink = '%s.html' % allComics[i+1].uid
		else:
			tomorrowLink = "#"
		
		if i > 0:
			yesterdayLink = '%s.html' % allComics[i-1].uid
		else:
			yesterdayLink = "#"
		
		# write an html page for it
		replacements = dict(
							theDate=thisComic.date,
							thePreviousComic=yesterdayLink,
							theNextComic=tomorrowLink,
							theComic='img/%s.gif' % thisComic.uid,
							theTitle=repairEntities(thisComic.title),
							theComment=repairEntities(thisComic.altText),
						)
		with open('comics/%s.html'%thisComic.uid,'w') as f:
			f.write(str(Template(tmpl, searchList=[replacements])))
	return
	

comic_url_re = re.compile(r'href="(.*?)"')
comic_date_re = re.compile(r'(\d+?)/(\d+)/(\d+)')
def process_month(month_url, month_text):
	
	nodes = BeautifulSoup(month_text)
	#print unicode(nodes.findAll('div',{'class':'one_record'}), errors='ignore')
	#print unicode(nodes.prettify(), errors='ignore')
	# added the unicode ignore bits because of Téodor is like the Steve Irwin of causing UnicodeDecodeErrors
	# if having non-ascii codepoints in your given name was a piano Téodor would be considered a bold and unpredictable new talent --fish
	for record in nodes.findAll('div',{'class':'one_record'}):
		do_comic(record)
		#unionpool.spawn_n(do_comic, record)

def do_comic(record):
	this_url=""
	this_month=""
	this_day=""
	this_year=""
	m = comic_url_re.search(str(record))
	if m:
		this_url = m.group(1)

	m = comic_date_re.search(str(record))
	if m:
		this_month, this_day, this_year = (m.group(1), m.group(2), m.group(3))

	this_uid = "%s%s%s" % (this_year, this_month, this_day)
	friendly_date = '%s %s %s' % (this_day, months[this_month], this_year)

	print "------------> %s" % this_uid
	fetch_comic(this_uid, prefix+this_url, friendly_date)



# the old title_re was yielding the word 'date' for all the titles but thankfully I am the Thomas Edison of handing a crappy HTML page its ass
# this new one works now but it is not an ontological semantic web sort of solution but I don't know how those work anyway --fish
title_re = re.compile(r'<h2>(.*?)&nbsp;')

def fetch_comic(uid, url, dateString):
	
	if os.path.exists("comics/img/%s.gif"%uid) and Comic.select(Comic.q.uid==uid).count():
		print "%s: cached in DB and FS" % (uid)
		return
	
	try:
		day_text = urllib2.urlopen(url).read()
	except urllib2.HTTPError, erm:
		print "fetch_comic(): HTTP FAIL: url %s" % url
		print "fetch_comic(): HTTP FAIL: error %s" % erm
		sys.exit(2)
	
	nodes = BeautifulSoup(day_text)
	content = nodes.find('div',{'id':'content'})
	img = content.find('img')
	m = title_re.search(str(content.find('h2')))
	
	title = m.group(1)
	img_url = img['src']
	alt_text = img['title']
	
	# here I added some stuff to the output so as to better understand things --fish
	try:
		theComic = Comic(title=title,
						 altText=alt_text,
						 date=dateString,
						 uid=uid)
		uniprint("%s: TITLE\t\t %s" % (uid, title.encode(defaultencoding, 'ignore')))
		if alt_text:
			uniprint(u"%s: ALTTXT\t (%s)" % (uid, alt_text))
		else:
			uniprint(u"%s: ALTTXT\t (%s)" % (uid, ""))
	except DuplicateEntryError:
		uniprint("%s: DBDUPE\t" % uid)
	
	if not os.path.exists("comics/img/%s.gif"%uid):
		full_url = "%s%s"%(prefix[:-1],img_url)
		uniprint(u"%s: COMIC\t\t Fetching from %s"%(uid, full_url))
		
		try:
			sourceImg = urllib2.urlopen(full_url)
		except urllib2.HTTPError, erm:
			print "fetch_comic(): HTTP FAIL: url %s" % full_url
			print "fetch_comic(): HTTP FAIL: error %s" % erm
			sys.exit(2)
		
		#destImg = open('comics/img/%s.gif'%uid, 'w')
		with open('comics/img/%s.gif'%uid, 'w') as destImg:
			shutil.copyfileobj(sourceImg, destImg)
	else:
		print "%s: cached in FS"%(uid)

# unicode is a great idea man but I have no idea what the deal is with the 'asset bar' encoding schizophrenia
# so please excuse this function it's not a thing I'm proud of
def uniprint(out, enc=defaultencoding):
	if type(out) == types.UnicodeType:
		try:
			print u'%s' % out.decode(enc, 'ignore')
		except UnicodeEncodeError, erm:
			print "UnicodeEncodeError -- %s" % erm
		except UnicodeDecodeError, erm:
			print "UnicodeDecodeError -- %s" % erm
	elif type(out) == types.StringType:
		print out



months={'01':'jan',
		'02':'feb',
		'03':'mar',
		'04':'apr',
		'05':'may',
		'06':'jun',
		'07':'jul',
		'08':'aug',
		'09':'sep',
		'01':'jan',
		'2':'feb',
		'3':'mar',
		'4':'apr',
		'5':'may',
		'6':'jun',
		'7':'jul',
		'8':'aug',
		'9':'sep',
		'10':'oct',
		'11':'nov',
		'12':'dec',
		}

if __name__ == '__main__':
	main()
