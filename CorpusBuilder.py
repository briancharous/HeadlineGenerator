import feedparser
import sqlite3
import calendar
import requests
import json
import datetime
import argparse
import sys
import logging

class headlineDownloader:

	def getURLSFromWaybackMachineInDateRange(self, start, end, rssurl, quiet = False):
		origurl = rssurl
		if rssurl[0:7] == 'http://':
			# strip off http:// since the wayback machine doesn't want it and will return false if it gets that
			rssurl = rssurl[7:]
		elif rssurl[0:8] == 'https://':
			rssurl = rssurl[8:]

		urls = []

		logging.info('Searching for feeds for %s' % rssurl)
		startDate = start.strftime('%Y%m%d')
		endDate = end.strftime('%Y%m%d')
		payload = {'url': rssurl, 'fl' : 'timestamp', 'from' : startDate, 'end' : endDate}
		r = requests.get('http://web.archive.org/cdx/search/cdx', params = payload)
		if r.status_code == requests.codes.ok:
			timestamps = r.text.split() # api call returns plain text of timestamps separated by newline characters
			for timestamp in timestamps:
				url = 'https://web.archive.org/web/%s/%s' % (timestamp, origurl)
				urls.append(url)

		if not quiet:
			sys.stdout.write('\r')
			sys.stdout.flush()

		logging.info('Found %i urls for %s' % (len(urls), rssurl))

		return urls

	def downloadHeadlinesFromURL(self, rssurl, baseurl):
		""" 
		Download and parse an RSS feed and store the headlines in the database
		baseurl is the url of the live feed
		rssurl is the url where the feed is located

		rssurl and baserul can be the same, but if dealing with the Wayback Machine, baseurl is the url that gets
		inserted into the database, rssurl is the location of the url in the Wayback Machine
		"""
		logging.info('Downloading feed %s' % rssurl)
		fp = feedparser.parse(rssurl)
		for entry in fp.entries:
			headline = entry.title
			pubDate = calendar.timegm(entry.published_parsed) # convert to unix time UTC
			storyURL = entry.link
			query = "INSERT OR REPLACE INTO headlines (headline, date, feedURL, linkURL) VALUES (?, ?, ?, ?)"
			self.cursor.execute(query, (headline, pubDate, baseurl, storyURL))
		self.dbcon.commit()

	def createHeadlinesTable(self):
		"""
		Create a table in the database to store the headlines if it does not exist
		"""
		query = "CREATE TABLE IF NOT EXISTS headlines (headline TEXT NOT NULL, date INTEGER, feedURL TEXT, linkURL text NOT NULL, PRIMARY KEY (headline, linkURL))"
		self.cursor.execute(query)	
		self.dbcon.commit()

	def closeDBConnection(self):
		""" shutdown the connection to the database """
		self.dbcon.close()

	def openDBConnection(self):
		""" open a connection to the database """
		self.dbcon = sqlite3.connect('headlines.db')

	def __init__(self):
		self.dbcon = None
		self.openDBConnection()
		self.cursor = self.dbcon.cursor()
		self.createHeadlinesTable()
		logging.basicConfig(filename='status.log', level=logging.INFO)
		requests_log = logging.getLogger('requests')
		requests_log.setLevel(logging.WARNING)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-s', '--start_date', required = True, help = 'Date to start downloading feeds. Formatted YYYY-mm-dd')
	parser.add_argument('-e', '--end_date', required = True, help = 'Date to stop downloading feeds. Formatted YYYY-mm-dd')
	parser.add_argument('-f', '--feed', required = True, help = 'URL of rss feed')
	parser.add_argument('-q', '--quiet', required = False, action = 'store_true', help = 'Do not produce any output')
	args = parser.parse_args()

	startDate = datetime.datetime.strptime(args.start_date, '%Y-%m-%d')
	endDate = datetime.datetime.strptime(args.end_date, '%Y-%m-%d')
	baseurl = args.feed
	quiet = args.quiet

	h = headlineDownloader()
	now = datetime.datetime.now()
	if not quiet:
		print 'Searching the Wayback Machine for urls...'
	urls = h.getURLSFromWaybackMachineInDateRange(startDate, endDate, baseurl, quiet)
	if not quiet:
		print 'Found %i urls in date range' % len(urls)
		print 'Downloading feeds...'
	for i, url in enumerate(urls):
		if not quiet:
			sys.stdout.write('\r%i/%i' % (i+1, len(urls))) 
			sys.stdout.flush()
		h.downloadHeadlinesFromURL(url, baseurl)
	if not quiet:
		sys.stdout.write('\r')
		sys.stdout.flush()
		print 'Downloaded headlines from %i snapshots of %s' % (len(urls),  baseurl) 
	logging.info('Downloaded headlines from %i snapshots of %s' % (len(urls),  baseurl))

if __name__ == '__main__':
	main()