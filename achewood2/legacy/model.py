#!/usr/bin/env python
# encoding: utf-8
"""
model.py

Created by Christian Swinehart on 2007-08-17.
Crapola added later by FI$H 2000 as indicated.
Copyright (c) 2007, 2010 Samizdat Drafting Co. All rights reserved.
"""

import sys
import os
from sqlobject import *

database_filename = "achewood.db"

class Comic(SQLObject):
	title = UnicodeCol()
	altText = UnicodeCol()
	date = StringCol()
	#link = StringCol()
	uid = StringCol(length=8, alternateID=True)



# dude why you got to do a hardcoded path url thing? what it is now is the achewood db file defaults to the current dir in place of hardcode --fish
sqlhub.processConnection = connectionForURI('sqlite://%s/%s' % (
	os.getcwd(),
	database_filename,
))



# wrote all this print statement nonsense --fish
if not os.path.exists(os.path.join(os.getcwd(), database_filename)):
	print "YO DOGG: no database file up ins. Creating..."
	Comic.createTable(ifNotExists=True)
else:
	print "YO DOGG: using existing achewood.db"













def main():
	if len(sys.argv)>1 and sys.argv[1] == 'clear':
		print "YO DOGG: Clearing db"
		Comic.dropTable(True)
	Comic.createTable(ifNotExists=True)



if __name__ == '__main__':
	main()

