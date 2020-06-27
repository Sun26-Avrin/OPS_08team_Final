#!/usr/bin/python
import sys,requests, time,numpy, math
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from flask import Flask,render_template,request
from nltk import word_tokenize

app = Flask(__name__)

es_host = "127.0.0.1"
es_port = "9200"
es = Elasticsearch([{'host':es_host,'port':es_port}],timeout=30)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/word',method=['GET','POST'])
def word():
    return render_template('final.html',value=result)

@app.route('/tf')
def tf():
    return render_template('tf.html')

@app.route('/cosine')
def tf():
    return render_template('cosine.html')