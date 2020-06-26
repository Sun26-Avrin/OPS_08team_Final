from flask import Flask
from flask import render_template
from flask import request

from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import operator as op

from bs4 import BeautifulSoup
import requests

from elasticsearch import Elasticsearch
import time

from nltk.tokenize import word_tokenize as word_tk

app = Flask(__name__)
id=0

#Connect
es = Elasticsearch([{'host':"127.0.0.1",'port':"9200"}],timeout=30)

@app.route('/')

def index():

	return render_template('index.html')


# Elastic에 데이터 단일 삽입
@app.route('/insert',methods= ['POST','GET'])
def insert():
	#Calculate Time & Set Result
	global id
	SOF="" #삽입 성공 여부
	s_time=time.time() #시간 시작
	total_words=0 #전체 단어수
	url = request.form['single']
	page = requests.get(url)
	soup = BeautifulSoup(page.content,'html.parser')
	text = soup.get_text().replace("\n"," ")
	
	p_time=time.time()-s_time #크롤링 끝	

	#Calculate Total_Words (Including Stop Words)
	total_words=len(text.split())

	#Create Index 
	if es.indices.exists(index="ops_project"):
		pass
	else :
		es.indices.create(index="ops_project")
	
	#Doc & Check
	doc={'url':url, 'text':text, 'processing_time':p_time}
	es.indices.refresh(index="ops_project") #refresh 해줘야 바로 검색가능
	res=[]
	res=es.search(index="ops_project", body= {"query":{"match":{"url":url}}} )
	
	#Insert Into Elastic
	if((res['hits']['total'] == 0) or (res['hits']['hits'][0]['_source']['url']!=url)) :
		es.index(index="ops_project",doc_type="string",id=id, body=doc)
		id+=1
		SOF="Successfully Inserted!"
		
		return render_template('index.html', p_time=p_time, total_words=total_words,SOF=SOF, url=url)
	else :
		SOF="already Exists..!"
		es.indices.refresh(index="ops_project") #refresh
		res1=res['hits']['hits'][0]['_source']['url']

		return render_template('index.html',p_time=p_time, total_words=total_words, SOF=SOF, url=url)

# 파일저장 및 데이터송신
@app.route('/file',methods= ['POST','GET'])
def file():
	if request.method == 'POST':
		f = request.files['group']
		f.save(f.filename)
		GSOF='1'
		f = open(f.filename,'r')
		lines = f.readlines()
		dic={}
		for i in range(len(lines)) :
			dic[i]=lines[i] 
		return render_template('index.html',GSOF=GSOF,lines=dic,list_len=len(lines))
	else :
		GSOF='0'
		return render_template('index.html',GSOF=GSOF)


# 파일처리 후 엘라스틱서치 (총 단어수, 처리시간, 분석버튼 두개, 성공여부 디스플레이 필수)
@app.route('/file_processing',methods= ['POST','GET'])
def file_processing():
	if request.method == 'POST':
		global id
		url = []
		texts = []
		navi_list=[] # 한번에 출력하기위한 네비게이터(성공한것만)
		SOF_list={} # 성공 실패여부 기록	
		list_len = request.form['list_len']
		for i in range(int(list_len)) :
			lines=request.form[str(i)]
			if(len(lines)<8):
				continue
			url.append(lines)

		for i in range(len(url)):
			s_time=time.time() #크롤링 시작
			total_words=0    #전체 단어수
			page = requests.get(url[i])
			soup = BeautifulSoup(page.content,'html.parser')
			text = soup.get_text().replace("\n"," ")
			p_time=time.time()-s_time #크롤링 끝
			
			#Calculate Total_Words (Including Stop Words)
			total_words=len(text.split())
			
			#Create Index 
			if es.indices.exists(index="ops_project"):
				pass
			else :
				es.indices.create(index="ops_project")
	
			#Doc & Check
			doc={'url':url[i], 'text':text, 'total_words':total_words ,'processing_time':p_time}
			es.indices.refresh(index="ops_project") #refresh 해줘야 바로 검색가능
			res=[]
			res=es.search(index="ops_project", body= {"query":{"match":{"url":url[i]}}} )
		
			#Insert Into Elastic
			if((res['hits']['total'] == 0) or (res['hits']['hits'][0]['_source']['url']!=url[i])) :
				es.index(index="ops_project",doc_type="string",id=id, body=doc)
				id+=1
				SOF_list[url]='성공!'
				es.indices.refresh(index="ops_project") #refresh
				res=es.search(index="ops_project", body= {"query":{"match":{"_id":(id-1)}}})
				navi_list.append(res)

			else :
				SOF_list[url]='중복!'
				es.indices.refresh(index="ops_project") #refresh	
				
			
			
		
		
		return render_template('index.html',id_list,navi)

			
 


# Show TF-IDF Top 10
@app.route('/tf_idf',methods= ['POST','GET'])
def tf_idf():

		
	url = []
	texts = []	
	list_len = request.form['list_len']
	for i in range(int(list_len)) :
		lines=request.form[str(i)]
		if(len(lines)<8):
			continue
		url.append(lines)

	for i in range(len(url)):
		page = requests.get(url[i])
		soup = BeautifulSoup(page.content,'html.parser')

		text = soup.get_text().replace("\n"," ")
		texts.append(text)
	

	# 여기서부터 TF-IDF 계산
	doc = []

	tf_v1 = TfidfVectorizer(stop_words='english') #sublinear_tf=True
	tf_array=tf_v1.fit_transform(texts).toarray()
	features=sorted(tf_v1.vocabulary_.items())

	for j in range(len(texts)):
		dic={}
		seq={}
		
		for idx in range(len(tf_array[j])):
			seq[idx]=tf_array[j][idx]
	
		s_dict=sorted(seq.items(),key=op.itemgetter(1),reverse=True)

		for i in range(10) :
			dic[features[s_dict[i][0]][0]]=s_dict[i][1]
	
		doc.append(dic)
	
	# 여기서 TF-IDF끝
	return render_template('index.html',doc=doc)
	


@app.route('/test',methods= ['POST','GET'])
def test():
	if request.method == 'POST' :
		url = []	
		list_len = request.form['list_len']
		for i in range(int(list_len)) :
			lines=request.form[str(i)]
			if(len(lines)<8):
				continue
			url.append(lines)
		type2 = type(lines)	
		line_len=len(lines)
		lines = request.form
		return render_template('index.html',line=lines,url=url,type2=type2,list_len=line_len)


@app.route('/test2',methods= ['POST','GET'])
def test2():
	data = request.form
	
	return render_template('index.html',data=data)


		
	
	
	
	



if __name__ == '__main__' :
	app.run(debug=True)





