"""
HeadlineGenerator.py 
Brian Charous

This program generates headlines from a given corpus using a Markov Chain
"""

from CorpusBuilder import LanguageModel
import marshal
import random
import sys
import re

class BadSeedException(Exception):
	pass

def readLanguageModel(filename):
	"""
	Read language model from a file
	"""

	with open(filename, 'r') as f:
		model = LanguageModel()
		data = marshal.load(f)
		model.trigramCounts = data[0]
		model.bigramCounts = data[1]
		model.unigramCounts = data[2]
		model.possibleWordsGivenBigram = data[3]
		model.possibleWordsGivenUnigram = data[4]
		model.tagCounts = data[5]
		model.tagCountsForWord = data[6]
		model.tagSequenceCounts = data[7]

	return model

def getNextToken(currentTokens, model):
	"""
	Given a list of tokens in a headline and a language model, generate a suitable next token
	"""

	# try trigram
	if len(currentTokens) > 1:
		previousBigram = currentTokens[-2:]
		if (previousBigram[0], previousBigram[1]) in model.possibleWordsGivenBigram:

			# get a list of all the next possible words and pick one of the most probable ones randomly 
			possibleWords = list(model.possibleWordsGivenBigram[(previousBigram[0], previousBigram[1])])
			if possibleWords:
				probs = model.getProbabilitiesOfTrigrams(previousBigram[0], previousBigram[1], possibleWords)
				sortedByProbs = sorted(probs, key = lambda tup: tup[1])
				top = sortedByProbs[0:20]

				# if the headline is less than 8 tokens long, delete the '<END>' token, otherwise recursively backtrack
				if len(currentTokens) < 8 and len(top) > 1:
					try:
						endIndex = [token[0] for token in top].index('<END>')
						del top[endIndex]
					except ValueError, e:
						pass
				if not top:
					currentTokens[-1] = getNextToken(currentTokens[:-1], model)
					return getNextToken(currentTokens, model)
				rand = random.randint(0, len(top) - 1)
				return top[rand][0]

	# the same as the trigrams except for bigrams. runs if there are less than 2 tokens in the headline or a given bigram never occurs
	previousUnigram = currentTokens[-1]
	if previousUnigram in model.possibleWordsGivenUnigram:
		possibleWords = list(model.possibleWordsGivenUnigram[previousUnigram])
		if possibleWords:
			probs = model.getProbabilitiesOfBigrams(previousUnigram, possibleWords)
			sortedByProbs = sorted(probs, key = lambda tup: tup[1], reverse = True)
			top = sortedByProbs[0:20]
			if len(currentTokens) < 8 and len(top) > 1:
				try:
					endIndex = [token[0] for token in top].index('<END>')
					del top[endIndex]
				except ValueError, e:
					pass
			if not top:
				# print currentTokens
				currentTokens[-1] = getNextToken(currentTokens[:-1], model)
				# print currentTokens
				return getNextToken(currentTokens, model)
			rand = random.randint(0, len(top) - 1)
			return top[rand][0]


	# only get here if the seed was not in the corpus
	raise BadSeedException()

def generateHeadlines(seed, model):
	"""
	Loop and generate tokens until an end token is found, format the resulting string
	"""
	tokens = seed.split()
	while True:
		next = getNextToken(tokens, model)
		tokens.append(next)
		if next == '<END>':
			break

	sentence = ""
	regex = re.compile(r'[A-z0-9$&]')
	for i, token in enumerate(tokens[:-1]):
		if regex.match(token):
			# word found, put spaces
			if not (tokens[i-1] == "$" or tokens[i-1] == "-"):
				sentence = sentence + " " + token
			else: 
				sentence = sentence + token
		else:
			sentence = sentence + token
	return sentence[1:]

def main():
	print "Reading language model"
	if len(sys.argv) < 2:
		print 'Usage: python %s model_filename' % sys.argv[1]

	model = readLanguageModel(sys.argv[1])
	while True:
		seed = raw_input("Seed: ")
		try:
			print generateHeadlines(seed, model)
		except BadSeedException:
			print "Error: seed '%s' not found in corpus" % seed

if __name__ == '__main__':
	main()