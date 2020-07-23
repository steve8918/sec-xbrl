# Copyright 2014 Altova GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import feedparser
import os.path
import sys, getopt
import time
import socket
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import xml.etree.ElementTree as ET
import zipfile
import zlib
import random


edgarNamespaces = [{'edgar': 'http://www.sec.gov/Archives/edgar'}, {'edgar': 'https://www.sec.gov/Archives/edgar'}]
cik_list = {}


def read_ticket_txt():
	f = open('ticker.txt', 'r')
	file = f.read()
	x = file.split("\n")
	for y in x:
		w = y.split("\t")
		if cik_list.get(w[1]):
			continue
		cik_list[w[1]] = w[0]


def downloadfile( sourceurl, targetfname ):
	mem_file = ""
	good_read = False
	xbrlfile = None
	if os.path.isfile( targetfname ):
		print( "Local copy already exists" )
		return True
	else:
		print( "Downloading:", sourceurl )
		try:
			xbrlfile = urlopen( sourceurl )
			try:
				mem_file = xbrlfile.read()
				good_read = True
			finally:
				xbrlfile.close()
		except HTTPError as e:
			print( "HTTP Error:", e.code )
		except URLError as e:
			print( "URL Error:", e.reason )
		except TimeoutError as e:
			print( "Timeout Error:", e.reason )
		except socket.timeout:
			print( "Socket Timeout Error" )
		if good_read:
			output = open( targetfname, 'wb' )
			output.write( mem_file )
			output.close()
		return good_read


def getTargetDirectory(cik_number):
	cik_number = cik_number.lstrip('0')
	ticker = cik_list.get(cik_number, cik_number).upper()

	if not os.path.exists( "sec/" + ticker):
		os.makedirs( "sec/" + ticker)
	target_dir = "sec/" + ticker + '/'
	return target_dir


def SECdownload(year, month):
	root = None
	feedFile = None
	feedData = None
	good_read = False
	itemIndex = 0

	feed_filename = 'xbrlrss-' + str(year) + '-' + str(month).zfill(2) + '.xml'
	feed_directory = 'sec/rss/'
	edgarFilingsFeed = 'http://www.sec.gov/Archives/edgar/monthly/{}'.format(feed_filename)
	print( edgarFilingsFeed )

	target_feed_filename = feed_directory + feed_filename
	if not downloadfile(edgarFilingsFeed, target_feed_filename):
		raise Exception("Could not download " + edgarFilingsFeed)

	feedData = open(target_feed_filename, 'r').read()

	# we have to unfortunately use both feedparser (for normal cases) and ET for old-style RSS feeds,
	# because feedparser cannot handle the case where multiple xbrlFiles are referenced without enclosure
	try:
		root = ET.fromstring(feedData)
	except ET.ParseError as perr:
		print( "XML Parser Error:", perr )
	feed = feedparser.parse( feedData )
	try:
		print( feed[ "channel" ][ "title" ] )
	except KeyError as e:
		print( "Key Error:", e )

	# Process RSS feed and walk through all items contained
	for item in feed.entries:
		print( item[ "summary" ], item[ "title" ], item[ "published" ] )
		try:
			# Identify ZIP file enclosure, if available
			enclosures = [ l for l in item[ "links" ] if l[ "rel" ] == "enclosure" ]
			if ( len( enclosures ) > 0 ):
				# ZIP file enclosure exists, so we can just download the ZIP file
				enclosure = enclosures[0]
				sourceurl = enclosure[ "href" ]
				cik = item[ "edgar_ciknumber" ]

				target_dir = getTargetDirectory(str(cik))
				targetfname = target_dir + str(year) + "-" + str(month).zfill(2) + "-" + sourceurl.split('/')[-1]
				print(targetfname)

				retry_counter = 3
				while retry_counter > 0:
					good_read = downloadfile( sourceurl, targetfname )
					if good_read:
						break
					else:
						print( "Retrying:", retry_counter )
						retry_counter -= 1
			else:
				# We need to manually download all XBRL files here and ZIP them ourselves...
				linkname = item[ "link" ].split('/')[-1]
				linkbase = os.path.splitext(linkname)[0]
				cik = item[ "edgar_ciknumber" ]

				target_dir = getTargetDirectory(str(cik))

				zipfname = target_dir+cik+'-'+linkbase+"-xbrl.zip"
				print(zipfname)
				if os.path.isfile( zipfname ):
					print( "Local copy already exists" )
					continue

				currentItem = list(root.iter( "item" ))[itemIndex]
				xbrlFiling = None
				xbrlFilesItem = None
				xbrlFiles = None

				for edgarNamespace in edgarNamespaces:
					xbrlFiling = currentItem.find( "edgar:xbrlFiling", edgarNamespace )
					if not xbrlFiling:
						continue

					xbrlFilesItem = xbrlFiling.find( "edgar:xbrlFiles", edgarNamespace )
					xbrlFiles = xbrlFilesItem.findall( "edgar:xbrlFile", edgarNamespace )
					break

				if not xbrlFiling:
					raise Exception("can't find xbrlFiling")

				temp_zip_dir = target_dir + "temp" + str(random.randint(1,1000000)) + "/"
				if not os.path.exists(temp_zip_dir):
					os.makedirs(temp_zip_dir)

				zf = zipfile.ZipFile( zipfname, "w" )

				try:
					for xf in xbrlFiles:
						xfurl = xf.get( "{http://www.sec.gov/Archives/edgar}url" )
						if xfurl.endswith( (".xml",".xsd") ):
							targetfname = temp_zip_dir + xfurl.split('/')[-1]
							print(targetfname)
							retry_counter = 3
							while retry_counter > 0:
								good_read = downloadfile( xfurl, targetfname )
								if good_read:
									break
								else:
									print( "Retrying:", retry_counter )
									retry_counter -= 1
							if not os.path.isfile(targetfname):
								continue

							zf.write( targetfname, xfurl.split('/')[-1], zipfile.ZIP_DEFLATED )
							os.remove( targetfname )
				finally:
					zf.close()
					os.rmdir(temp_zip_dir)
		except KeyError as e:
			print( "Key Error:", e )
		except:
			print( "ERROR", itemIndex, item[ "summary" ], item[ "title" ], item[ "published" ], item["links"] )
			raise
		finally:
			print( "----------" )
		itemIndex += 1

def main(argv):

	read_ticket_txt()

	if not os.path.exists("sec/"):
		os.makedirs( "sec/")
	if not os.path.exists("sec/rss"):
		os.makedirs( "sec/rss")

	year = 2013
	month = 1
	from_year = 1999
	to_year = 2020
	year_range = False
	if not os.path.exists( "sec" ):
		os.makedirs( "sec" )
	socket.setdefaulttimeout(10)
	start_time  = time.time()
	try:
		opts, args = getopt.getopt(argv,"hy:m:f:t:",["year=","month=","from=","to="])
	except getopt.GetoptError:
		print( 'loadSECfilings -y <year> -m <month> | -f <from_year> -t <to_year>' )
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print( 'loadSECfilings -y <year> -m <month> | -f <from_year> -t <to_year>' )
			sys.exit()
		elif opt in ("-y", "--year"):
			year = int(arg)
		elif opt in ("-m", "--month"):
			month = int(arg)
		elif opt in ("-f", "--from"):
			from_year = int(arg)
			year_range = True
		elif opt in ("-t", "--to"):
			to_year = int(arg)
			year_range = True
	if year_range:
		if from_year == 1999:
			from_year = to_year
		if to_year == 1999:
			to_year = from_year
		for year in range( from_year, to_year+1 ):
			for month in range( 1, 12+1 ):
				SECdownload( year, month )
	else:
		SECdownload( year, month )
	end_time = time.time()
	print( "Elapsed time:", end_time - start_time, "seconds" )

if __name__ == "__main__":
	main(sys.argv[1:])
