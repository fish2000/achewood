import os, re, urlparse
from django.db import models
from django.db.models import signals
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import models as auth_models
from django.contrib.auth.management import create_superuser
from datetime import datetime, date
from imagekit.models import ImageModel, ICCImageModel
from achewood2.utils.monkeypatch import memoize

# local-ish
pf = FileSystemStorage(location="%s" % settings.MEDIA_ROOT)
urlspec = re.compile("\W+", re.IGNORECASE)
urlend = re.compile("\-$", re.IGNORECASE)

@memoize
def AWGetURLTitle(urlstr):
	## umlaut subs from http://code.activestate.com/recipes/576507-sort-strings-containing-german-umlauts-in-correct-/
	urlstr = urlstr.lower().replace(
			u'\xe4', u'a'
		).replace(
			u'\xf6', u'o'
		).replace(
			u'\xfc', u'u'
		).encode('iso-8859-1')
	return u'%s' % unicode(urlend.sub('', urlspec.sub('-', urlstr)).lower())

#
# managers
#
class AWCalendarMonthManager(models.Manager):
	def month(self, yyyy, mm):
		d = date(yyyy, mm, 1)
		try:
			return self.objects.get(calendardate=d)
		except ObjectDoesNotExist:
			return AWCalendarMonth(calendardate=d)

#
# models
#
class AWBaseMorsel(models.Model):
	class Meta:
		abstract = True
	
	createdate = models.DateTimeField('Created on',
		default=datetime.now,
		blank=True,
		editable=False)
	modifydate = models.DateTimeField('Last modified on',
		default=datetime.now,
		blank=True,
		editable=False)
	visible = models.BooleanField("Visible",
		default=True,
		editable=True)
	title = models.CharField(verbose_name="Title",
		default="",
		unique=False,
		blank=True,
		max_length=255)
	urlstring = models.CharField(verbose_name="URL String",
		default="",
		unique=False,
		blank=True,
		null=True,
		max_length=255)
	
	def save(self, force_insert=False, force_update=False):
		self.modifydate = datetime.now()
		self.urlstring = AWGetURLTitle(self.title)
		if len(self.urlstring) < 1:
			self.urlstring = AWGetURLTitle(self.pk)
		super(AWBaseMorsel, self).save(force_insert, force_update)
	
	def __unicode__(self):
		return u'%s' % self.title
	
	def __str__(self):
		return str(self.title)



class AWBaseImage(ImageModel):
	class Meta:
		abstract = True
		verbose_name = "base image"
		verbose_name_plural = "base images"
	
	class IKOptions:
		spec_module = 'achewood2.localache.imagespecs'
		cache_dir = '_ikcache'
		#icc_dir = '_ikicc'
		image_field = 'image' # confusatron
		storage = pf
	
	@staticmethod
	def _gettargetpath():
		return os.path.join(
			settings.MEDIA_ROOT,
			AWImage._meta.get_field('image').upload_to
		)
	targetpath = property(_gettargetpath)
	
	image = models.ImageField(verbose_name="Image",
		storage=pf,
		null=True,
		blank=True,
		upload_to='images/_comics',
		height_field='h',
		width_field='w',
		max_length=255)
	w = models.IntegerField(verbose_name="width",
		editable=False,
		null=True)
	h = models.IntegerField(verbose_name="height",
		editable=False,
		null=True)
	createdate = models.DateTimeField('Created on',
		default=datetime.now,
		blank=True,
		editable=False)
	modifydate = models.DateTimeField('Last modified on',
		default=datetime.now,
		blank=True,
		editable=False)
	visible = models.BooleanField("Visible",
		default=True,
		editable=True)
	caption = models.CharField(verbose_name="Caption",
		default="",
		unique=False,
		blank=True,
		null=True,
		max_length=255)
	
	def save(self, force_insert=False, force_update=False):
		self.modifydate = datetime.now()
		super(AWBaseImage, self).save(force_insert, force_update)
	
	@memoize
	def _get_hash(self):
		return FSGetHashForFilePath(self.image.path)
	imagehash = property(_get_hash)
	
	@memoize
	def get_absolute_url(self):
		return u"%s" % self.image.url
	
	def __str__(self):
		if len(self.caption) > 1:
			return "%s (%s)" % (self.id, strip_tags(self.caption))
		else:
			return "%s" % self.id
	
	def __unicode__(self):
		return u"" + self.__str__()


class AWImage(AWBaseImage):
	class Meta:
		abstract = False
		verbose_name = "achewood strip image file"
		verbose_name_plural = "achewood strip image files"


class AWComic(AWBaseMorsel):
	class Meta:
		abstract = False
		verbose_name = "achewood strip"
		verbose_name_plural = "achewood strips"
	
	image = models.ForeignKey(AWImage,
		verbose_name="Comic Image",
		blank=True,
		null=True,
		editable=True)
	imageurl = models.URLField(verbose_name="Original Image URL",
		verify_exists=False,
		default=None,
		unique=False,
		blank=True,
		null=True,
		max_length=255)
	postdate = models.DateField('Posted on',
		default=date.today,
		blank=True,
		null=True,
		editable=True)
	alttext = models.CharField(verbose_name="Alt Text",
		default="",
		unique=False,
		blank=True,
		max_length=255)
	alturl = models.URLField(verbose_name="Alt URL",
		verify_exists=False,
		default=None,
		unique=False,
		blank=True,
		null=True,
		max_length=255)
	asseturlstring = models.CharField(verbose_name="Strip Assetbar.com URL String",
		#default=None,
		unique=True,
		blank=False,
		null=False,
		max_length=16)
	dialogue = models.TextField(verbose_name="Transcribed Dialogue",
		default="",
		blank=True,
		null=True,
		editable=True)
	
	def _get_asseturl(self):
		return "http://m.assetbar.com/achewood/%s" % self.asseturlstring
	def _set_asseturl(self, nurlstr):
		if nurlstr.startswith('http://m.assetbar.com/achewood/'):
			self.asseturlstring = os.path.basename(urlparse.urlparse(nurlstr).path)
	def _del_asseturl(self):
		self.asseturlstring = None
	asseturl = property(_get_asseturl, _set_asseturl, _del_asseturl)

class AWCalendarMonth(AWBaseMorsel):
	class Meta:
		abstract = False
		verbose_name = "archive calendar month"
		verbose_name_plural = "archive calendar months"
	
	objects = AWCalendarMonthManager()
	calendardate = models.DateField('First date',
		#default=date.today,
		unique=True,
		blank=False,
		null=False,
		editable=True)
	data = models.TextField(verbose_name="Archive Data",
		default="",
		blank=True,
		null=True,
		editable=True)
	url = models.URLField(verbose_name="Archive URL",
		verify_exists=False,
		default=None,
		unique=False,
		blank=True,
		null=True,
		max_length=255)

signals.post_syncdb.disconnect(
	create_superuser,
	sender=auth_models,
	dispatch_uid='django.contrib.auth.management.create_superuser')

def create_testuser(app, created_models, verbosity, **kwargs):
	if not settings.DEBUG:
		return
	try:
		auth_models.User.objects.get(username='fish')
	except auth_models.User.DoesNotExist:
		#logg.info('Creating test user: fish')
		print '*' * 80
		print 'Creating test user -- login: fish, password: eatshit'
		print '*' * 80
		assert auth_models.User.objects.create_superuser('fish', 'fish2000@gmail.com', 'eatshit')
	else:
		#logg.info('Test user fish already exists.')
		print 'Test user fish already exists.'

signals.post_syncdb.connect(
	create_testuser,
	sender=auth_models,
	dispatch_uid='common.models.create_testuser')
