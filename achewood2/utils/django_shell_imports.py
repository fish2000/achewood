
## setup django
from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.conf import settings
from django.db import models, connection
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ObjectDoesNotExist

import datetime
from imagekit.models import ImageModel
from tagging.fields import TagField
from tagging.models import Tag

## import achewood2 specifics
from achewood2.localache.models import AWComic, AWImage
from achewood2.utils import importstrips as strips

## web scraping stuff
from BeautifulSoup import BeautifulSoup
import re, urllib2, string, os, sys

