from CorpusBuilder import LanguageModel
import marshal
import random
import sys
import re

class BadSeedException(Exception):
	pass

def readLanguageModel(filename):
	with open(filename, 'r') as f:
		model = LanguageModel()
		data = marshal.load(f)
		model.trigramCounts = data[0]
		model.bigramCounts = data[1]
		model.unigramCounts = data[2]
		model.possibleWordsGivenBigram = data[3]
		model.possibleWordsGivenUnigram = data[4]

	return model

def getNextToken(currentTokens, model):
	if len(currentTokens) > 1:
		previousBigram = currentTokens[-2:]
		if (previousBigram[0], previousBigram[1]) in model.possibleWordsGivenBigram:
			possibleWords = list(model.possibleWordsGivenBigram[(previousBigram[0], previousBigram[1])])
			if possibleWords:
				probs = model.getProbabilitiesOfTrigrams(previousBigram[0], previousBigram[1], possibleWords)
				sortedByProbs = sorted(probs, key = lambda tup: tup[1])
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


	raise BadSeedException()

def generateHeadlines(seed, model):
	
	tokens = seed.split()
	while True:
		next = getNextToken(tokens, model)
		tokens.append(next)
		# print tokens
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
	model = readLanguageModel(sys.argv[1])
	while True:
		seed = raw_input("Seed: ")
		try:
			print generateHeadlines(seed, model)
		except BadSeedException:
			print "Error: seed '%s' not found in corpus" % seed

if __name__ == '__main__':
	main()