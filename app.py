#!/usr/bin/python
import sys
import requests
import time
import numpy
import math
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from flask import Flask
from flask import render_template
from flask import request
from nltk import word_tokenize
app = Flask(__name__)

result=[]
count = 0
es_host = "127.0.0.1"
es_port = "9200"
es = Elasticsearch([{'host':es_host,'port':es_port}],timeout=30)

@app.route('/')
def index():
    return render_template('index.html')
