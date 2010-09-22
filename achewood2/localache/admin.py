import os
from django.conf import settings
from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned


class AWNimda(admin.ModelAdmin):
	save_as = True
	save_on_top = True
	actions_on_top = True
	actions_on_bottom = True

class AWComicAdmin(AWNimda):
	list_display = ('visible','postdate','asseturlstring','title','alttext','dialogue','with_alturl')
	list_display_links = ('title','asseturlstring')
	list_filter = ('visible',)
	search_fields = ['title', 'asseturlstring', 'alttext', 'dialogue']
	def with_alturl(self, obj):
		yesno = obj.alturl.startswith('http://m.assetbar.com/achewood/one_strip') and "img/admin/icon-no.gif" or "img/admin/icon-yes.gif"
		return u'<a href="%s"><img src="%s" alt="Huh" /></a>' % (
			#obj.id and ("/admin/localache/awcomic/%s/" % obj.id) or '#',
			obj.alturl.startswith('http://m.assetbar.com/achewood/one_strip') and "#" or obj.alturl,
			os.path.join(settings.ADMIN_MEDIA_PREFIX, yesno),
		)
	with_alturl.short_description = "Alt URL?"
	with_alturl.allow_tags = True
	

