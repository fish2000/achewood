from django.contrib import admin
from achewood2.localache.models import AWComic, AWImage, AWCalendarMonth
from achewood2.localache.admin import AWComicAdmin

class AWAdminSite(admin.AdminSite):
	pass

adminsite = AWAdminSite()
adminsite.index_template = "admin/index.html"

adminsite.register(AWComic, AWComicAdmin)
adminsite.register(AWImage)
adminsite.register(AWCalendarMonth)


