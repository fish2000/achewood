#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement

import sys

from django.core.management import setup_environ
from achewood2 import settings
setup_environ(settings)

try:
	import re2 as re
except ImportError:
	import re
else:
	re.set_fallback_notification(re.FALLBACK_WARNING)

import os, urllib2, urlparse, datetime
from django.db.models import Q
from django.utils.html import strip_tags, strip_entities
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.template.loader import render_to_string
from BeautifulSoup import BeautifulSoup, UnicodeDammit
from achewood2.utils.monkeypatch import memoize
from achewood2.localache.models import AWComic, AWImage, AWCalendarMonth


def soup(url):
	uh = urllib2.urlopen(url)
	u = uh.read()
	uh.close()
	return BeautifulSoup(u)

title_re = re.compile(r'<h2>(.*?)&nbsp;')
monthly_re = re.compile(r"archive\?start=\d\d\d\d\d\d\d\d")
sre = re.compile('(\w\w\w\w)|(1st)')
monthnames = ('Never', "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december")
monthabbrevs = [m[0:3] for m in monthnames]

def monthindex(monthname):
	try:
		return monthnames.index(monthname)
	except ValueError:
		try:
			return monthabbrevs.index(monthname)
		except ValueError:
			return -1
	return -1

def AWAchewoodDate(yyyy, mm, dd):
	""" works also for yy years """
	return "%02d%02d%04d" % (int(mm), int(dd), (int(yyyy) < 100 and (2000+int(yyyy)) or int(yyyy)))

def AWAssetbarDate(yyyy, mm, dd):
	return "%04d%02d%02d" % ((int(yyyy) < 100 and (2000+int(yyyy)) or int(yyyy)), int(mm), int(dd))

def AWAchewoodURL(yyyy, mm, dd):
	return "http://achewood.com/index.php?date=%s" % AWAchewoodDate(yyyy, mm, dd)

@memoize
def AWAssetbarURLStringsForMonth(yyyy=None, mm=None, data=None):
	"""
	Returns a dict of assetbar.com archive strings,
	keyed by Achewood dates (not AWAssetbarDate dates!)
	"""
	if not data:
		archurl = "http://m.assetbar.com/achewood/archive?start=%s" % AWAssetbarDate(yyyy, mm, 1)
		records = soup(archurl).findAll('div', {'class': "one_record"})
	else:
		records = BeautifulSoup(data).findAll('div', {'class': "one_record"})
	
	return dict(zip(
		map(lambda r: unicode(r.find('div', {'class':"title"}).contents[2]).replace('/', ''), records),
		map(lambda r: r.find('a')['href'], records),
	))

@memoize
def AWAssetbarURL(yyyy=None, mm=None, dd=None, urlstring=None):
	if not urlstring:
		archdate = AWAchewoodDate(yyyy, mm, dd)
		archmonthstrings = AWAssetbarURLStringsForMonth(yyyy, mm)
		if archdate in archmonthstrings:
			urlstring = archmonthstrings[archdate]
		else:
			return None
	return "http://m.assetbar.com/achewood/%s" % urlstring

@memoize
def AWGetStripAssetbarData(yyyy=None, mm=None, dd=None, urlstring=None):
	"""
	Get a tuple of AsssetBar.com data for a given date.
	
	returns something like this:
	(
		img, 			# url to the strip image data
		title, 			# title string (from <title> of page)
		alttxt, 		# alt text from strip <img> tag
		prev,			# 'prev' assetbar url string
		next,			# 'next' assetbar url string
	)
	... any of whose members might be None if it couldn't be sorted out.
	"""
	if not urlstring:
		assetbarurl = AWAssetbarURL(yyyy, mm, dd)
		nodes = soup(assetbarurl)
		#urlstring = AWAssetbarURLStringsForMonth(yyyy, mm)[AWAchewoodDate(yyyy, mm, dd)]
		urlstring = assetbarurl.replace('http://m.assetbar.com/achewood/', '')
	else:
		nodes = soup(AWAssetbarURL(urlstring=urlstring))
	
	content = nodes.find('div',{'id':'content'})
	date = content.find('h2').find('span', {'class':"date"}).contents[0].split('/')
	img = content.find('img')
	m = title_re.search(unicode(content.find('h2')))
	
	title = m.group(1)
	img_url = urlparse.urljoin('http://m.assetbar.com/', img['src'], allow_fragments=False)
	alt_text = img['title']
	month, day, year = date[0], date[1], date[2]
	
	prevnext = dict(map(lambda a: (sre.search(a.string).group(), a['href']), nodes.find('span', {'class': "prevnext"}).findAll('a')))
	
	prevnext.update({
		'urlstring': urlstring,
		'month': month,
		'day': day,
		'year': year,
		'imgurl': img_url,
		'title': title,
		'alttxt': alt_text,
	})
	return prevnext

@memoize
def AWGetStripAchewoodData(yyyy=None, mm=None, dd=None, urlstring=None):
	"""
	Get a tuple of Achewood.com data for a given date
	
	returns this:
	(
		alttxt,			# alt text from strip <img> tag
		url,			# url the strip points to when clicked
						# (usually an m.assetbar.com url but sometimes different)
	)
	
	"""
	if urlstring:
		bar = AWGetStripAssetbarData(urlstring=urlstring)
		yyyy, mm, dd = bar['year'], bar['month'], bar['day']
	
	nodes = soup(AWAchewoodURL(yyyy, mm, dd))
	
	try:
		alttxt = nodes.find('p', {'id':"comic_body"}).find('img')['title']
	except TypeError:
		alttxt = ""
	
	return {
		'alttxt': alttxt,
		'url': nodes.find('p', {'id':"comic_body"}).find('a')['href'],
	}

#@memoize
def AWGetStripDialogue(yyyy=None, mm=None, dd=None, urlstring=None):
	"""
	Get a strip's dialogue from ohnorobot.com for a given date.
	
	This works by taking a URL like this:
	"http://www.ohnorobot.com/index.pl?s=%s+%s+%s&Search=Search&comic=636&e=0&n=0&b=0&m=0&d=0&t=0" % (
		monthnames[mm], dd, yyyy
	)
	... and looking up the specific AWAchewoodDate in the mess of return data to find the dialogue.
	
	"""
	if urlstring:
		bar = AWGetStripAssetbarData(urlstring=urlstring)
		yyyy, mm, dd = bar['year'], bar['month'], bar['day']
	
	dsurl = "http://www.ohnorobot.com/index.pl?s=%s+%s+%s&Search=Search&comic=636&e=0&n=0&b=0&m=0&d=0&t=0" % (
		monthnames[int(mm)], dd, yyyy
	)
	dsearch = soup(dsurl)
	dlg = filter(lambda li: li.find('a', {'class':"searchlink", 'href':re.compile("%s$" % AWAchewoodDate(yyyy, mm, dd))}), dsearch.findAll('li'))
	
	if len(dlg) == 1:
		#return strip_entities(strip_tags(dlg.pop()))
		return strip_tags(dlg.pop())
	return u""

@memoize
def AWGetStripData(yyyy=None, mm=None, dd=None, urlstring=None):
	if urlstring:
		bar = AWGetStripAssetbarData(urlstring=urlstring)
		yyyy, mm, dd = bar['year'], bar['month'], bar['day']
	else:
		bar = AWGetStripAssetbarData(yyyy, mm, dd)
		urlstring = bar['urlstring']
	
	out = bar
	out.update({
		'url': AWGetStripAchewoodData(yyyy, mm, dd).get('url'),
		'dialogue': AWGetStripDialogue(yyyy, mm, dd),
	})
	return out

@memoize
def AWGetAssetbarMonths(url="http://m.assetbar.com/achewood/archive"):
	pageText = urllib2.urlopen(url).read()
	index_pages = [u.split('=')[1] for u in monthly_re.findall(pageText)]
	return map(lambda m: (m[0:4], m[4:6]), index_pages)

def AWGetFilenameForURL(url, default=None):
	urlpieces = urlparse.urlparse(str(url))
	try:
		return os.path.basename(urlpieces[2])
	except IndexError:
		return default
	return default

def AWGetSuffixForURL(url, default=None):
	fn = AWGetFilenameForURL(url, default)
	if fn:
		if not fn.rfind('.') == -1:
			try:
				return fn.rsplit('.', 1)[1].lower()
			except IndexError:
				return default
	return default

def AWGetTemporaryFileForURL(url, **kwargs):
	if str(url).startswith('http'):
		suffix = "gif"
		if 'suffix' in kwargs:
			suffix = kwargs['suffix']
			del kwargs['suffix']
		
		itemp = NamedTemporaryFile(suffix=(".%s" % suffix), **kwargs)
		
		try:
			itemp.write(urllib2.urlopen(url).read())
		except urllib2.URLError, urlerr:
			itemp.close()
			itemp = None
		else:
			itemp.flush()
		return itemp
	else:
		return None



# backported from original script
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
	return fixedText

def main(argv=None):
	mths = get_months()
	get_data(mths)
	
	cmx = AWComic.objects.filter(visible=True).order_by('postdate')
	
	get_alturls(cmx)
	get_dialogue(cmx)
	
	get_images(cmx)
	generate_pages(cmx)
	return 0


def get_months():
	print "Getting archive months from main URL..."
	mths = AWGetAssetbarMonths()
	print "Got %s total months" % len(mths)
	
	for yyyy, mm in mths:
		mth = AWCalendarMonth.objects.month(yyyy, mm)
		if not mth.id:
			print "Caching month: %s %s" % (monthnames[int(mm)].capitalize(), yyyy)
			mth.url = "http://m.assetbar.com/achewood/archive?start=%s" % AWAssetbarDate(yyyy, mm, 1)
			mth.data = urllib2.urlopen(mth.url).read()
			mth.title = "%s %s" % (monthnames[int(mm)], yyyy)
			mth.save()
	return mths


def get_data(mths=None):
	
	if not mths:
		print "Getting archive months from main URL..."
		mths = AWGetAssetbarMonths()
		print "Got %s total months" % len(mths)
	
	for yyyy, mm in mths:
		mth = AWCalendarMonth.objects.month(yyyy, mm)
		if not mth.id:
			print "Caching month: %s %s" % (monthnames[int(mm)].capitalize(), yyyy)
			mth.url = "http://m.assetbar.com/achewood/archive?start=%s" % AWAssetbarDate(yyyy, mm, 1)
			mth.data = urllib2.urlopen(mth.url).read()
			mth.title = "%s %s" % (monthnames[int(mm)], yyyy)
			mth.save()
		
		bar = AWAssetbarURLStringsForMonth(data=mth.data)
		print "%s %s: %s strips" % (monthnames[int(mm)].capitalize(), yyyy, len(bar))
		
		for d, strip in bar.items():
			
			
			try:
				c = AWComic.objects.get(asseturlstring=strip)
			except ObjectDoesNotExist:
				#data = AWGetStripData(yyyy, int(mm), dd)
				try:
					dd = int(d[2:4])
					data = AWGetStripAssetbarData(yyyy, int(mm), dd)
				except ValueError:
					data = AWGetStripAssetbarData(urlstring=strip)
				
				print u">>>\t %s\t %s" % (
					d, data['title']
				)
				
				c = AWComic()
				c.postdate = datetime.date(
					int(data['year']),
					int(data['month']),
					int(data['day']),
				)
				c.title = repairEntities(data['title'])
				c.alttext = repairEntities(data['alttxt'])
				c.asseturlstring = data['urlstring']
				c.imageurl = data['imgurl']
				
				#c.alturl = data['url']
				#c.dialogue = data['dialogue']
				c.alturl = 'later'
				c.dialogue = 'later'
				
				c.save()
			else:
				print "---\t %s\t %s" % (d, c.title,)
			
		print ""
	
	print ""

def get_alturls(comix=None):
	if comix == None:
		comix = AWComic.objects.filter(visible=True).order_by('postdate')
	
	print ""
	
	print "Getting alternative URLs for %s cached comics..." % comix.count()
	for c in comix.filter(Q(alturl__istartswith="later") | Q(alturl__isnull=True) | Q(alturl__exact="")):
		yyyy, mm, dd = (c.postdate.year, c.postdate.month, c.postdate.day)
		c.alturl = AWGetStripAchewoodData(yyyy, mm, dd).get('url')
		c.save()
		print "---\t %s\t %s" % (c.assetbardate, c.alturl)

def get_dialogue(comix=None):
	if comix == None:
		comix = AWComic.objects.filter(visible=True).order_by('postdate')
	
	print ""
	
	print "Getting dialogue for %s cached comics..." % comix.count()
	for c in comix.filter(Q(dialogue__istartswith="later") | Q(alturl__isnull=True)):
		yyyy, mm, dd = (c.postdate.year, c.postdate.month, c.postdate.day)
		c.dialogue = AWGetStripDialogue(yyyy, mm, dd)
		c.save()
		print "---\t %s\t %s ..." % (c.assetbardate, c.dialogue[0:100])

def get_images(comix=None):
	if comix == None:
		comix = AWComic.objects.filter(visible=True).order_by('postdate')
	
	print ""
	print "Getting images for %s cached comics..." % comix.count()
	
	for c in comix:
		
		print ""
		
		try:
			im = c.awimage
			if im == None:
				print "WTF: NoneType found for c.awimage (comic %s)" % c.id
				raise ObjectDoesNotExist
			
		except ObjectDoesNotExist:
			suffix = AWGetSuffixForURL(c.imageurl, default='gif')
			tn = "%s.%s" % (c.assetbardate, suffix)
			where = os.path.join(AWImage.gettargetpath(), tn)
			
			if os.path.exists(where):
				ff = File(open(where, 'r'))
				print "---\t Existing image file: %s" % tn
			else:
				ff = File(AWGetTemporaryFileForURL(c.imageurl, suffix=suffix))
				print ">>>\t New image file: %s" % tn
				
			if ff:
				cim = AWImage()
				cim.comic = c
				cim.image.save(tn, ff)
				cim.save()
				
				print ">>>\t New image object: %s" % os.path.basename(cim.image.name)
		else:
			print "---\t Existing image object: %s" % os.path.basename(im.image.name)
	
	print ""

def generate_pages(comix=None):
	if comix == None:
		comix = AWComic.objects.filter(visible=True).order_by('postdate')
	
	for i in xrange(comix.count()):
		this_comic = comix[i]
		print "Processing HTML for %s" % this_comic.assetbardate
		
		if i < comix.count() - 1:
			nextpage = '%s.html' % comix[i+1].assetbardate
		else:
			nextpage = "#"
		
		if i > 0:
			previouspage = '%s.html' % comix[i-1].assetbardate
		else:
			previouspage = "#"
		
		if not this_comic.alturl.startswith('http://m.assetbar.com/achewood/one_strip'):
			alturl = this_comic.alturl
		else:
			alturl = None
		
		tplout = os.path.join(settings.MEDIA_ROOT, "%s.html" % this_comic.assetbardate)
		if os.path.exists(tplout):
			os.remove(tplout)
		
		with open(tplout, 'w') as f:
			f.write(render_to_string("localache-django.html", {
				'nextpage': nextpage,
				'previouspage': previouspage,
				'title': this_comic.title,
				'postdate': "%02s %s %04s" % (
					this_comic.postdate.day,
					monthabbrevs[int(this_comic.postdate.month)].capitalize(),
					this_comic.postdate.year,
				),
				'comic': this_comic.imagename,
				'alttxt': this_comic.alttext,
				#'alturl': alturl,
			}).encode('utf-8'))
		
		
		


if __name__ == "__main__":
	sys.exit(main(argv=sys.argv))



