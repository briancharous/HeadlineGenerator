from CorpusBuilder import LanguageModel
import marshal
import random
import sys


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
				rand = random.randint(0, len(possibleWords)-1)
				return possibleWords[rand]

	previousUnigram = currentTokens[-1]
	if previousUnigram in model.possibleWordsGivenUnigram:
		possibleWords = list(model.possibleWordsGivenUnigram[previousUnigram])
		if possibleWords:
			rand = random.randint(0, len(possibleWords) - 1)
			return possibleWords[rand]

	raise BadSeedException()

def generateHeadlines(seed, model):
	
	tokens = seed.split()
	while True:
		next = getNextToken(tokens, model)
		tokens.append(next)
		# print tokens
		if next == '.' or next == '!' or next == '?':
			break
	return ' '.join(tokens)

def main():
	print "Reading language model"
	model = readLanguageModel(sys.argv[1])
	while True:
		seed = raw_input("Seed: ")
		print generateHeadlines(seed, model)

if __name__ == '__main__':
	main()