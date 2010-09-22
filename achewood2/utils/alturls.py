import sys

from django.core.management import setup_environ
from achewood2 import settings
setup_environ(settings)

import re, urllib2, urlparse, datetime
from django.core.exceptions import ObjectDoesNotExist
from achewood2.utils.monkeypatch import memoize
from achewood2.utils.importstrips import AWAchewoodDate
from achewood2.localache.models import AWComic, AWImage, AWCalendarMonth


def get_alturls():
	for c in AWComic.objects.exclude(alturl__istartswith="http://m.assetbar.com/"):
		print "---\t %s\t %s" % (AWAchewoodDate(c.postdate.year, c.postdate.month, c.postdate.day), c.alturl)








def main(argv):
	get_alturls()
	return 0

if __name__ == "__main__":
	sys.exit(main(argv=sys.argv))


