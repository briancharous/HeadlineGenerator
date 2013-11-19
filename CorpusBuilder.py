import feedparser
import sqlite3
import calendar
import requests
import json
import datetime
import argparse
import sys

class headlineDownloader:

	def getURLFromWaybackMachineNearDate(self, date, rssurl):
		payload = {'url': rssurl, 'timestamp': date}
		r = requests.get("http://archive.org/wayback/available", params = payload)
		if r.status_code == requests.codes.ok:
			j = r.json()
			if 'archived_snapshots' in j:
				j = j['archived_snapshots']
				if 'closest' in j:
					snapshots = j['closest']
					available = snapshots['available']
					status = snapshots['status'] == '200'
					if available and status:
						return snapshots['url']

		raise WaybackUnavailableException("Wayback didn't return a snapshot url")

	def getURLSFromWaybackMachineInDateRange(self, start, end, rssurl, quiet = False):

		if rssurl[0:7] == 'http://':
			# strip off http:// since the wayback machine doesn't want it and will return false if it gets that
			rssurl = rssurl[7:]

		urls = []

		curDate = start
		delta = datetime.timedelta(days=1)
		while curDate <= end:
			if not quiet:
				sys.stdout.write('\rSearching for %s' % curDate.strftime('%Y-%m-%d'))
				sys.stdout.flush()
			try:
				epoch = calendar.timegm(curDate.timetuple())
				newUrl = self.getURLFromWaybackMachineNearDate(epoch, rssurl)
				urls.append(newUrl)
			except WaybackUnavailableException, e:
				print 'INFO: No snapshot found on ', curDate

			curDate += delta

		if not quiet:
			sys.stdout.write('\r')
			sys.stdout.flush()
		return urls

	def downloadHeadlinesFromURL(self, rssurl, baseurl):
		""" 
		Download and parse an RSS feed and store the headlines in the database
		baseurl is the url of the live feed
		rssurl is the url where the feed is located

		rssurl and baserul can be the same, but if dealing with the Wayback Machine, baseurl is the url that gets
		inserted into the database, rssurl is the location of the url in the Wayback Machine
		"""
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

class WaybackUnavailableException(Exception):
	pass

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

if __name__ == '__main__':
	main()