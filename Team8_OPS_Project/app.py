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


from nltk.corpus import stopwords
import nltk
nltk.download('stopwords')

from sklearn.metrics.pairwise import cosine_similarity

#url check
from urllib.request import urlopen
from urllib.error import URLError, HTTPError


app = Flask(__name__)
id=0

#cos similarity
def cos_sim(A,B):
	return

#누적 url
url_list=[]

#Connect
es = Elasticsearch([{'host':"127.0.0.1",'port':"9200"}],timeout=30)
#과제 채점 상황때 생길 오류 방지하기 위하여
if es.indices.exists(index="ops_project"):
	pass
else :
	es.indices.create(index="ops_project")
es.indices.delete(index='ops_project')  

# url check function
def url_check(url):
	try:
		res = urlopen(url)
		return 1
	except (HTTPError) :
		#0 as false
		return 0 
	except URLError : 
		return 0
	except ValueError :
		return 0
	
	

@app.route('/')

def index():
	if es.indices.exists(index="ops_project"):
		pass
	else :
		es.indices.create(index="ops_project")
	es.indices.refresh(index="ops_project")
	res=es.search(index="ops_project", body= {"query":{"match_all":{}}} )
	value=res['hits']['hits']

	return render_template('index.html',value=value)


# Elastic에 데이터 단일 삽입
@app.route('/insert',methods= ['POST','GET'])
def insert():
	#Calculate Time & Set Result
	global id
	global url_list


	url = request.form['single']
	if(not(url_check(url))) : #유효성검사
		es.indices.refresh(index="ops_project")
		res=es.search(index="ops_project", body= {"query":{"match_all":{}}} )
		value=res['hits']['hits']
		return render_template('index.html',SOF="URL is not valid",value=value)
	 


	SOF="" #삽입 성공 여부
	s_time=time.time() #시간 시작
	total_words=0 #전체 단어수
	
	
	page = requests.get(url)
	soup = BeautifulSoup(page.content,'html.parser')
	text = soup.get_text().replace("\n"," ")
	url_list.append(url)
	
	p_time=time.time()-s_time #크롤링 끝	

	#Calculate Total_Words (Not Including Stop Words)
	total_words=len([i for i in text.split() if i not in stopwords.words('english')]) 

	#Create Index 
	if es.indices.exists(index="ops_project"):
		pass
	else :
		es.indices.create(index="ops_project")
	
	#Doc & Check
	doc={'url':url,'total_words': total_words, 'processing_time':p_time,'text':text }
	es.indices.refresh(index="ops_project") #refresh 해줘야 바로 검색가능
	res=[]
	res=es.search(index="ops_project", body= {"query":{"match":{"url":url}}} )
	
	#Insert Into Elastic
	if((res['hits']['total']['value'] == 0) or (res['hits']['hits'][0]['_source']['url']!=url)) :
		es.index(index="ops_project",doc_type="string",id=id, body=doc)
		id+=1
		SOF="Successfully Inserted!"
		
		
	else :
		SOF="already Exists..!"
	
	es.indices.refresh(index="ops_project")
	res=es.search(index="ops_project", body= {"query":{"match_all":{}}} )
	value=res['hits']['hits']

	return render_template('index.html',value=value, SOF=SOF, )

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
		global url_list
		url = []
		texts = []
		navi_list=[] # 한번에 출력하기위한 네비게이터(성공한것만)
		SOF_list={} # 성공 실패여부 기록	
		list_len = request.form['list_len']
		for i in range(int(list_len)) :
			lines=request.form[str(i)]
			if(lines==''): #공백처리
				continue
			if(not(url_check(lines))) : #유효하지않은 URL
				SOF_list[lines]="실패"
				continue
			url.append(lines)
			url_list.append(lines)
			SOF_list[lines]="성공"

		for i in range(len(url)):
			s_time=time.time() #크롤링 시작
			total_words=0    #전체 단어수
			page = requests.get(url[i])
			soup = BeautifulSoup(page.content,'html.parser')
			text = soup.get_text().replace("\n"," ")
			p_time=time.time()-s_time #크롤링 끝
			
			#Calculate Total_Words
			total_words=len([i for i in text.split() if i not in stopwords.words('english')])
			
			#Create Index 
			if es.indices.exists(index="ops_project"):
				pass
			else :
				es.indices.create(index="ops_project")
	
			#Doc & Check
			doc={'url':url[i],'total_words': total_words, 'processing_time':p_time,'text':text }
			es.indices.refresh(index="ops_project") #refresh 해줘야 바로 검색가능
			res=[]
			res=es.search(index="ops_project", body= {"query":{"match":{"url":url[i]}}} )
		
			#Insert Into Elastic
			if((res['hits']['total']['value'] == 0) or (res['hits']['hits'][0]['_source']['url']!=url[i])) :
				es.index(index="ops_project",doc_type="string",id=id, body=doc)
				id+=1
				SOF_list[url[i]]='성공'
				es.indices.refresh(index="ops_project") #refresh
				res=es.search(index="ops_project", body= {"query":{"match":{"_id":(id-1)}}})
				navi_list.append(res)

			else :
				SOF_list[url[i]]='중복'
				es.indices.refresh(index="ops_project") #refresh	
				
			
			
		
		es.indices.refresh(index="ops_project")
		res=es.search(index="ops_project", body= {"query":{"match_all":{}}} )
		value=res['hits']['hits']		

		return render_template('index.html',value=value, SOFL=(SOF_list))

			
 


# Show TF-IDF Top 10
@app.route('/tf_idf',methods= ['POST','GET'])
def tf_idf():

	global url_list
	f_url = request.form['tf_url']
	# Detect Error
	if( len(url_list) <2 ) :
		return render_template('tf_idf.html', e_code='1',f_url=f_url)
	# 변수설정
	data_len=es.search(index="ops_project", body= {"query":{"match_all":{}}} )['hits']['total']
		
	
	texts = []	
	list_len = data_len
	
	
	# 텍스트셋 만들기
	for i in range(len(url_list)):
		page = requests.get(url_list[i])
		soup = BeautifulSoup(page.content,'html.parser')

		text = soup.get_text().replace("\n"," ")
		texts.append(text)
	

	# 여기서부터 TF-IDF 계산
	#doc = []     #TF-IDF
	top_10 =[]   

	tf_v1 = TfidfVectorizer(stop_words='english') #sublinear_tf=True
	tf_array=tf_v1.fit_transform(texts).toarray()
	features=sorted(tf_v1.vocabulary_.items())
	
	# 단일문서 TF-IDF vector (해당 URL)
	
	d_idx = url_list.index(f_url)
	seq={} #매핑
	for idx in range(len(tf_array[d_idx])) :
		seq[idx]=tf_array[d_idx][idx]
	#정렬
	s_dict = sorted(seq.items(),key=op.itemgetter(1),reverse=True)
	
	#Vocab 추출
	for i in range(10) :
		#top_10[features[s_dict[i][0]][0]]=1
		top_10.append(features[s_dict[i][0]][0])

	'''
	#전체문서 TF-IDF vector
	for j in range(len(texts)):
		dic={}
		seq={}
		
		for idx in range(len(tf_array[j])):
			seq[idx]=tf_array[j][idx]
	
		s_dict=sorted(seq.items(),key=op.itemgetter(1),reverse=True)

		for i in range(10) :
			dic[features[s_dict[i][0]][0]]=s_dict[i][1]
	
		doc.append(dic)
	'''
	# 여기서 TF-IDF끝

	es.indices.refresh(index="ops_project")
	res=es.search(index="ops_project", body= {"query":{"match_all":{}}} )
	value=res['hits']['hits']
	

	return render_template('tf_idf.html', top_10=top_10, f_url=f_url , e_code=0 )
	


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


# 코사인 유사도
@app.route('/cos',methods= ['POST','GET'])
def cos():

	# 변수설정
	global url_list  #url 셋
	f_url = request.form['cos_url']
	if( len(url_list) < 4 ) :
		return render_template('cos.html',e_code='1',f_url=f_url)

	texts = []	
	list_len = es.search(index="ops_project", body= {"query":{"match_all":{}}} )['hits']['total']
	
	
	# 텍스트셋 만들기
	for i in range(len(url_list)):
		page = requests.get(url_list[i])
		soup = BeautifulSoup(page.content,'html.parser')

		text = soup.get_text().replace("\n"," ")
		texts.append(text)
	

	# 여기서부터 Cos 계산
	#doc = []     #TF-IDF
	top_3 =[]    

	tf_v1 = TfidfVectorizer(stop_words='english') #sublinear_tf=True
	tf_sparse=tf_v1.fit_transform(texts)
	features=sorted(tf_v1.vocabulary_.items())
	
	# 단일문서 TF-IDF vector (해당 URL)
	
	cos = cosine_similarity(tf_sparse[url_list.index(f_url)],tf_sparse)
	
	# 문서매핑
	cos_dic={}
	for i in range(len(url_list)):
		cos_dic[url_list[i]]=cos[0][i]
	
	# 문서 추출
	cos_sorted = sorted(cos_dic.items(),key=op.itemgetter(1),reverse=True)
	# top3
	#top_3.append(cos_sorted[0])
	top_3.append(cos_sorted[1])
	top_3.append(cos_sorted[2])
	top_3.append(cos_sorted[3])

	

	
	
	# 여기서 Cos 끝

	es.indices.refresh(index="ops_project")
	res=es.search(index="ops_project", body= {"query":{"match_all":{}}} )
	value=res['hits']['hits']
	

	return render_template('cos.html', cos=cos, f_url=f_url, top_3=top_3,e_code='0')


		
	
	
	
	



if __name__ == '__main__' :
	app.run(debug=True)





