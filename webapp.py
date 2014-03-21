from flask import Flask
from flask import jsonify
from flask import request
import HeadlineGenerator
import logging

app = Flask(__name__)
app.config['DEBUG'] = False

@app.route('/')
def printhello():
	return "hello world"

@app.route('/generate', methods=['GET'])
def genHeadline():
	seed = request.form['seed']
	result = ""
	try:
		result = HeadlineGenerator.generateHeadlines(seed, model)
	except HeadlineGenerator.BadSeedException:
		result = "Seed %s not found in corpus" % seed
	return jsonify(result=result)

def main():
	modelname = 'headlines.model'
	# logging.info("reading %s" % modelname)
	# print "reading %s" % modelname
	global model
	model = HeadlineGenerator.readLanguageModel(modelname)
	# logging.info("done reading model")
	# print "done reading model"

if __name__ == '__main__':
	main()
	app.run()
