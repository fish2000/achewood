from django.contrib import admin
from achewood2.localache.models import AWComic, AWImage

class AWAdminSite(admin.AdminSite):
	pass

adminsite = AWAdminSite()
adminsite.index_template = "admin/index.html"

adminsite.register(AWComic)
adminsite.register(AWImage)