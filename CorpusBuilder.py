"""
CorpusBuilder.py
Brian Charous

This file generates a corpus given a SQLite database of headlines
"""


import argparse
import sqlite3
import datetime
import calendar
import re
from collections import Set
import marshal
import pattern.en as pattern

class LanguageModel(object):

	def tokenizeHeadline(self, headline):
		""" deprecated tokenzier. now using pattern's tokenizer """
		groups = re.compile(r"""
			(?P<whitesp ace>\s+) |
			(?P<acronym>(?:\w\.){2,}) |
			(?P<abbreviation>\b(?:Mr.|Mrs.|Pres.|pres.)) |
			(?P<wordAp>\b\w+'\w*\b) |
			(?P<word>\b\w+\b) |
			(?P<punctuation>[\,\.\?\!\-\:\;\&\@\$])
			""", re.DOTALL | re.VERBOSE)

		tokens = []
		for match in re.finditer(groups, headline):
			whitespace, acronym, abbreviation, wordAp, word, punctuation = match.groups()
			token = None
			if abbreviation:
				token = match.group('abbreviation')
			if acronym:
				token = match.group('acronym')
			if wordAp:
				token = match.group('wordAp')
			if word:
				token = match.group('word')
			if punctuation:
				token = match.group('punctuation')
			if token is not None:
				tokens.append(token)

		if tokens:
			tokens.append('<END>')

		return tokens

	def addHeadlineToModel(self, headline):
		"""
		Count trigrams, bigrams, unigrams, tag sequences, and add them to the model for a given headline
		"""

		tags = pattern.tag(headline, tokenize = True)

		tokens = []

		if tags:
			tags.append(('<END>', '<END>'))

		weirdpunctuation = re.compile(r'\`|\"|\[|\]|\(|\)|\{|\}')

		for i, tag in enumerate(tags):
			# remove quotes, brackets
			if weirdpunctuation.match(tag[0]):
				del tags[i]

		for tag in tags:
			tokens.append(tag[0])

		# count unigrams
		for token in tokens:
			occurrences = self.unigramCounts.get(token, 0)
			occurrences += 1
			self.unigramCounts[token] = occurrences

		# count bigrams
		for i in xrange(0, len(tokens) - 1):
			t1 = tokens[i]
			t2 = tokens[i+1]
			bigram = (t1, t2)
			occurrences = self.bigramCounts.get(bigram, 0)
			occurrences += 1
			self.bigramCounts[bigram] = occurrences

			curPossibleWords = self.possibleWordsGivenUnigram.get(t1, set())
			curPossibleWords.add(t2)
			self.possibleWordsGivenUnigram[t1] = curPossibleWords

		# count trigrams
		for i in xrange(0, len(tokens) - 2):
			t1 = tokens[i]
			t2 = tokens[i+1]
			t3 = tokens[i+2]
			trigram = (t1, t2, t3)
			occurrences = self.trigramCounts.get(trigram, 0)
			occurrences += 1
			self.trigramCounts[trigram] = occurrences

			curPossibleWords = self.possibleWordsGivenBigram.get((t1, t2), set())
			curPossibleWords.add(t3)
			self.possibleWordsGivenBigram[(t1, t2)] = curPossibleWords


		#count tags

		for tagTouple in tags:
			tag = tagTouple[1]
			word = tagTouple[0]

			# count number of times word occurs as tag
			# dict of dicts
			# {word : {tag : tagcount}}
			tagCounts = self.tagCountsForWord.get(word, {})
			tagCount = tagCounts.get(tag, 0)
			tagCount += 1
			tagCounts[tag] = tagCount
			self.tagCountsForWord[word] = tagCounts

			# count raw tag counts
			curTagCount = self.tagCounts.get(tag, 0)
			curTagCount += 1
			self.tagCounts[tag] = curTagCount

		# count tag sequeunces
		for i in xrange(0, len(tags) - 1):
			prevTag = tags[i][1]
			curTag = tags[i+1][1]
			tagSequence = (prevTag, curTag)
			occurrences = self.tagSequenceCounts.get(tagSequence, 0)
			occurrences += 1
			self.tagSequenceCounts[tagSequence] = occurrences

	def getHeadlinesFromDatabaseInDateRange(self, startdate, enddate):
		""" Get a list of headlines from the SQLite database in between startdate and enddate datetime objects """

		startUnixTime = calendar.timegm(startdate.timetuple())
		endUnixTime = calendar.timegm(enddate.timetuple())
		query = "SELECT headline FROM headlines WHERE date > ? AND date < ?"

		headlines = []
		for row in self.cursor.execute(query, (startUnixTime, endUnixTime)):
			headlines.append(row[0])

		return headlines

	def buildModelInDateRange(self, startdate, enddate):
		headlines = self.getHeadlinesFromDatabaseInDateRange(startdate, enddate)
		for headline in headlines:
			self.addHeadlineToModel(headline)

	def getProbabilitiesOfTrigrams(self, word1, word2, potentialWords):
		"""
		Given two words and a list of potential words, computes the probabilities that each word in potential words comes next
		"""

		probabilities = []
		for potential in potentialWords:
			trigram = (word1, word2, potential)
			trigramcount = self.trigramCounts.get(trigram, 0)
			bigram = (word1, word2)
			bigramcount = self.bigramCounts.get(bigram, 0)
			assert bigramcount != 0
			probability = (float(trigramcount)/bigramcount) * self.probabilityOfTagToWord(self.mostProbableTagForWord(word2), potential)
			probabilities.append((potential, probability))

		return probabilities

	def getProbabilitiesOfBigrams(self, word, potentialWords):
		"""
		Given a and a list of potential words, computes the probabilities that each word in potential words comes next
		"""

		probabilities = []
		for potential in potentialWords:
			bigram = (word, potential)
			bigramcount = self.bigramCounts.get(bigram, 0)
			unigramcount = self.unigramCounts.get(word, 0)
			assert unigramcount != 0
			probability = (float(bigramcount)/unigramcount) * self.probabilityOfTagToWord(self.mostProbableTagForWord(word), potential)
			probabilities.append((potential, probability))
		return probabilities

	def mostProbableTagForWord(self, word):
		"""
		Returns the most likely tag for a given word
		"""

		tagsForWord = self.tagCountsForWord.get(word, {})
		highest = 0
		mostLikelyTag = None
		for tag, tagCount in tagsForWord.iteritems():
			if tagCount > highest:
				highest = tagCount
				mostLikelyTag = tag

		return mostLikelyTag

	def probabilityOfTagToWord(self, tag, word):
		"""
		Compute probability that a known tag goes to a potential word
		"""

		tagForWord = self.mostProbableTagForWord(word)
		if not tagForWord:
			return 0
		tagToTagCount = self.tagSequenceCounts.get((tag, tagForWord), 0)
		totalTagCount = self.tagCounts[tag]
		prob = float(tagToTagCount)/float(totalTagCount)
		return prob

	def openDBConnection(self):
		self.dbcon = sqlite3.connect('headlines.db')

	def closeDBConnection(self):
		self.dbcon.close()

	def __init__(self):
		self.dbcon = None
		self.openDBConnection()
		self.cursor = self.dbcon.cursor()
		self.trigramCounts = {}
		self.bigramCounts = {}
		self.unigramCounts = {}
		self.possibleWordsGivenBigram = {}
		self.possibleWordsGivenUnigram = {}
		self.tagCounts = {}
		self.tagCountsForWord = {}
		self.tagSequenceCounts = {}

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-s', '--start_date', required = True, help = 'Start date of headlines to build corpus from. Formatted YYYY-mm-dd')
	parser.add_argument('-e', '--end_date', required = True, help = 'End date of headlines to build corpus from. Formatted YYYY-mm-dd')
	parser.add_argument('-o', '--output', required = True, help = 'filename of output file')
	args = parser.parse_args()

	startDate = datetime.datetime.strptime(args.start_date, '%Y-%m-%d')
	endDate = datetime.datetime.strptime(args.end_date, '%Y-%m-%d')
	outputName = args.output

	starttime = datetime.datetime.now()
	model = LanguageModel()
	print "Building language model"
	model.buildModelInDateRange(startDate, endDate)
	model.closeDBConnection()

	try:
		endtime = datetime.datetime.now()
		timediff = endtime - starttime
		print "Language model computation took %s seconds" % timediff.seconds
		print "Writing to file"
		with open(outputName, 'w') as f:
			toMarshal = [model.trigramCounts, model.bigramCounts, model.unigramCounts, model.possibleWordsGivenBigram, model.possibleWordsGivenUnigram, model.tagCounts, model.tagCountsForWord, model.tagSequenceCounts]
			marshal.dump(toMarshal, f, 2)
			print "Language model written to %s" % outputName
	except IOError, e:
		print e

if __name__ == '__main__':
	main()
