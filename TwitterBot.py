"""
TwitterBot.py
Brian Charous

This program implements the Headline Generator and posts the headlines it generates to Twitter using a randomly
selected Google trending topic as the seed
"""


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
		""" 
		Get a list of trending topics on Google to use as a seed
		"""

		topics = []
		fp = feedparser.parse("http://www.google.com/trends/hottrends/atom/feed")
		for entry in fp.entries:
			topic = entry.title
			topics.append(topic)

		return topics

	def generateHeadline(self):
		"""
		Make the headline
		"""

		topics = self.getGoogleTrending()
		
		while True:
			rand = random.randint(0, len(topics)-1)
			topic = topics[rand]
			try:
				headline = HeadlineGenerator.generateHeadlines(topic, self.model)
				if headline != topic:
					return headline
				else:
					topics.remove(topic)
					logging.info("not enough data to generate headline for seed %s" % topic)
			except HeadlineGenerator.BadSeedException:
				logging.info("%s not in corpus", topic)
				topics.remove(topic)
			if not topics:
				logging.info("no trending topics in corpus")
				return None

	def postToTwitter(self):
		"""
		Make a headline and send the headline off to twitter
		"""

		headline = self.generateHeadline()
		if headline:
			logging.info("posting '%s'" % headline)
			self.twitter.PostUpdate(headline)

	def __init__(self, modelFilename):
		logging.basicConfig(filename = 'twitter_status.log', level = logging.INFO)
		self.twitter = twitter.Api(consumer_key = '', consumer_secret = '', access_token_key = '', access_token_secret = '')
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