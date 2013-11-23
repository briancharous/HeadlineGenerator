import HeadlineGenerator
import requests
import feedparser
import random
import twitter
from time import sleep
import sys
import logging

class TwitterBot:

	def getGoogleTrending(self):
		topics = []
		fp = feedparser.parse("http://www.google.com/trends/hottrends/atom/feed")
		for entry in fp.entries:
			topic = entry.title
			topics.append(topic)

		return topics

	def generateHeadline(self):

		topics = self.getGoogleTrending()
		
		while True:
			rand = random.randint(0, len(topics)-1)
			topic = topics[rand]
			try:
				return HeadlineGenerator.generateHeadlines(topic, self.model)
			except HeadlineGenerator.BadSeedException:
				logging.info("%s not in corpus", topic)
				topics.remove(topic)
			if not topics:
				logging.info("no trending topics in corpus")
				return None

	def postToTwitter(self):

		headline = self.generateHeadline()
		if headline:
			logging.info("posting '%s'" % headline)
			self.twitter.PostUpdate(headline)

	def __init__(self, modelFilename):
		logging.basicConfig(filename = 'twitter_status.log', level = logging.INFO)
		self.twitter = twitter.Api(consumer_key = 'Xdfb5x3sYS2Q8E7nYD6fw', consumer_secret = 'gETgfldkzFG1BpFVLcwa0pOo1V3P9vovh4MRAcl4s', access_token_key = '2210011554-xfUSAyljGxFt2h11uCQqOQuUA3UR8ZRkQJYRTNN', access_token_secret = 'StBOKpJZCUwmop63wvlnqFU4EUNPYE5ZSm1i4z3Gu6ZXG')
		logging.info("reading %s" % modelFilename)
		self.model = HeadlineGenerator.readLanguageModel(modelFilename)
		logging.info("done reading model")

def main():
	modelname = sys.argv[1]
	t = TwitterBot(modelname)
	while True:
		t.postToTwitter()
		sleep(600)

if __name__ == '__main__':
	main()