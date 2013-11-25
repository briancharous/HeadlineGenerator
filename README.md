NLP Headline Generator
=====================

Overview
-------------
This is a python program that generates bogus news headlines while simultaneously bringing joy to everyone it comes in contact with. 

Dependencies 
--------------
Python 2.7.x, python-twitter, pattern, requests, feedparser

Acquiring the data
--------------------
Included with this program is a corpus of headlines in a SQLite database as well as the generated corpus itself. To download more headlines, use `HeadlineDownloader.py`. Find an RSS feed and make sure it exists in the Wayback Machine (archive.org). Then, run `python HeadlineDownloader.py -s YYYY-mm-dd -e YYYY-mm-dd -f feedURL` where `-s` is the start date to download from and `-e` is the end date. To build the model once data is acquired, run `python CorpusBuilder.py -s YYYY-mm-dd -e YYYY-mm-dd -o modelfilename`. Note that this process may take a long time depending on the size of the corpus. PyPy is strongly recommended for this process.

Running
---------
Once the corpus is generated, run `python HeadlineGenerator.py modelfilename`. 

Running the Twitterbot
-----------------------
Get Twitter API keys, insert them into TwitterBot.py, then run `python TwitterBot.py modelfilename`