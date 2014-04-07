from flask import Flask
from flask import jsonify
from flask import request
import HeadlineGenerator
import logging

app = Flask(__name__)
app.config['DEBUG'] = True
modelname = 'headlinesxxsmall.model'
model = HeadlineGenerator.readLanguageModel(modelname)

@app.route('/generate', methods=['POST', 'OPTIONS'])
@crossdomain(origin='*')
def genHeadline():
	seed = request.form['seed']
	result = ""
	global model
	try:
		result = HeadlineGenerator.generateHeadlines(seed, model)
	except HeadlineGenerator.BadSeedException:
		result = "Seed %s not found in corpus" % seed
	return jsonify(result=result)

if __name__ == '__main__':
	app.run()
