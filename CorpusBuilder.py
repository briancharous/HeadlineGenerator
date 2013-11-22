import argparse
import sqlite3
import datetime
import calendar
import re
from collections import Set
import marshal

class LanguageModel(object):

	def tokenizeHeadline(self, headline):
		groups = re.compile(r"""
			(?P<whitespace>\s+) |
			(?P<acronym>(?:\w\.){2,}) |
			(?P<abbreviation>\b(?:Mr.|Mrs.|Pres.|pres.)) |
			(?P<wordAp>\b\w+'\w*\b) |
			(?P<word>\b\w+\b) |
			(?P<punctuation>[,\.\?\!])
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
				tokens.append(token.lower())

		if tokens and (tokens[-1] != '?' or tokens[-1] != '!' or tokens[-1] != '.'):
			tokens.append('.')

		return tokens

	def addHeadlineToModel(self, headline):

		tokens = self.tokenizeHeadline(headline)

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

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-s', '--start_date', required = True, help = 'Start date of headlines to build corpus from. Formatted YYYY-mm-dd')
	parser.add_argument('-e', '--end_date', required = True, help = 'End date of headlines to build corpus from. Formatted YYYY-mm-dd')
	parser.add_argument('-o', '--output', required = True, help = 'filename of output file')
	args = parser.parse_args()

	startDate = datetime.datetime.strptime(args.start_date, '%Y-%m-%d')
	endDate = datetime.datetime.strptime(args.end_date, '%Y-%m-%d')
	outputName = args.output

	model = LanguageModel()
	print "Building language model"
	model.buildModelInDateRange(startDate, endDate)
	model.closeDBConnection()

	try:
		print "Writing to file"
		with open(outputName, 'w') as f:
			toMarshal = [model.trigramCounts, model.bigramCounts, model.unigramCounts, model.possibleWordsGivenBigram, model.possibleWordsGivenUnigram]
			marshal.dump(toMarshal, f, 2)
			print "Language model written to %s" % outputName
	except IOError, e:
		print e

if __name__ == '__main__':
	main()
