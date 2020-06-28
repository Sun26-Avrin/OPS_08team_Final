#!/usr/bin/python
import sys, requests,time,numpy,math
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from flask import Flask,render_template,request
from nltk import word_tokenize
app = Flask(__name__)

result=[]
count = 0
es_host = "127.0.0.1"
es_port = "9200"
es = Elasticsearch([{'host':es_host,'port':es_port}],timeout=30)


def make_vector(word_list,word_dic):
    v =[]
    for w in word_dic.keys():
        val =0
        for t in word_list:
            if t==w:
                val+=1
        v.append(val)
    return v

def compute_tf(word_list):
    bow=set()
    wordcount_d={}

    for word in word_list:
        if word not in wordcount_d.keys():
            wordcount_d[word]=0
        wordcount_d[word]+=1
        bow.add(word)


    tf_d={}
    for word,count in wordcount_d.items():
        tf_d[word]=count/float(len(bow))
    
    return tf_d

def compute_idf(word_list,count):
    Dval = count
    bow=set()

    for i in range(count):
        tokenized = word_list[i]
        for tok in tokenized:
            bow.add(tok)


    idf_d={}
    for t in bow:
        cnt=0
        for s in word_list:
            if t in s:
                cnt+=1

        idf_d[t]=math.log(Dval/cnt)

    return idf_d

@app.route('/')
def helo_world():
    return render_template('final.html')

@app.route('/info', methods=['GET','POST'])
def info():
    global count
    output_list=[]
    word_count={}
    start = time.time()

    error = None
    if request.form['submit'] == 'oneUrl':
        url1 = request.form['name']

        req = requests.get(url1)
        html = req.text
        soup = BeautifulSoup(html,'html.parser')
        my_para = soup.select('body > div')
    
        for para in my_para:
            content = para.getText().split()

            for word in content:
                symbols = """!@#$%%^&*()_-+={[]}|/\;:"'.,<>?`"""
                for i in range(len((symbols))):
                    word = word.replace(symbols[i],'')
                if len(word)> 0:
                    output_list.append(word)
            
            
            for word in output_list:
                if word in word_count:
                    word_count[word]+=1
                else:
                    word_count[word]=1


        clock = time.time()-start

        list1 = list(word_count.keys())
        list2 = list(word_count.values())
        index_list = []
        index_list = es.indices.get('*')
        index_list = sorted(index_list,reverse=True)        
        info={
                "url":url1,
                "word":list1,
                "numWord":len(list1),
               #"frequency":list2,
                "time":clock,
                "dict":word_count

        }
        

        es.index(index='knu',doc_type ='student',id=count,body=info)
        count+=1
        es.indices.refresh(index='knu')

        query={"query":{"bool":{"must":[{"match":{"_type":'student'}}]}}}

        result = es.search(index='knu',body=query)
        result = result['hits']['hits']
        return render_template('final.html',value=result)


@app.route('/analyze', methods=['GET','POST'])
def info2():

    word_dict={}
    word_list=[]
    vec_list=[]
    url_list=[]
    url_list2=[]
    cos_res=[]
    cos_res2=[]

    numWord=[]
    find_list=[]

    dict_simil={}
    tf_d={}
    idf_d={}
    tidf_dic={}
    if request.method=='POST':
        

        for i in range(count):
            query={"query":{"bool":{"must":[{"match":{"_id":i}}]}}}
            docs=es.search(index='knu',body=query)

            if docs['hits']['total']['value']>0:
                for doc in docs['hits']['hits']:
                    word_dict.update(doc['_source']['dict'])
                    word_list.append(doc['_source']['word'])
                    url_list.append(doc['_source']['url'])
                    numWord.append(doc['_source']['numWord'])
        


        url2 = request.form['hid']
        query={"query":{"bool":{"must":[{"match":{"url":url2}}]}}}
        docs=es.search(index='knu',body=query)
        find_list=docs['hits']['hits'][0]['_source']['word']

        if request.form['Cosine']=='cosine':

            for i in range(count):
                vec_list.append(make_vector(word_list[i],word_dict))

            v1=make_vector(find_list,word_dict)
       
            for i in range(count):
                dotpro=numpy.dot(v1,vec_list[i])
                cossimil=dotpro/(numpy.linalg.norm(v1)*numpy.linalg.norm(vec_list[i]))
                cos_res.append(cossimil)
                dict_simil[url_list[i]]=cossimil

            cos_list = sorted(dict_simil.items(),key = lambda x:x[1],reverse=True)
            return render_template('analyze.html',value2=cos_list[1:])
        
        #tf-idf
        elif request.form['tf-idf']=='tfidf':

            idf_d = compute_idf(word_list,count)
            tf_d = compute_tf(find_list)

            for word,tfval in tf_d.items():
                tidf_dic[word]=tfval*idf_d[word]

            word_list = sorted(tidf_dic.items(),key = lambda x:x[1],reverse=True)
            return render_template('analyze.html',value2=word_list[:10])

if __name__ == '__main__' :
	app.run(debug=True)