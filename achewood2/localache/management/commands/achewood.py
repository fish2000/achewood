import sys
#from pprint import pprint
from django.db.models.loading import cache
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ImproperlyConfigured
from optparse import make_option

class Command(BaseCommand):
	help = ('Manage and view local achewood.com archive.')
	args = '[apps]'
	#requires_model_validation = True
	#can_import_settings = True

	def handle(self, *args, **options):
		pass
	
