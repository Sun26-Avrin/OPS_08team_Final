#!/bin/bash

# 디렉토리생성
echo "Create All The Directory..."
mkdir templates
mkdir static
mkdir static/image

# 파일 이동
echo "Placing All The File to Right Place..."
mv Untitled2.png static/image/Untitled2.png
mv index.html templates/index.html
mv cos.html templates/cos.html
mv tf_idf.html templates/tf_idf.html

# Mac OS 패키지설치 & 엘라스틱서치 ON
#brew services start elasticsearch
#brew install scikit-learn

# Ubuntu 패키지설치 & 엘라스틱서치 ON
#python -m pip show scikit-learn  #설치위치 보여줌
echo Installing sklearn Package...!
sudo pip install scikit-learn  #sklearn 설치
sleep 5
#./bin/elasticsearch -d #엘라스틱서치가 현재폴더에 있다고 가정
# 엘라스틱 서치 대기...
echo "we're waiting until ElasticSearch is on board for 20 sec"

i=1

while [ $i -lt 21 ]
do
        echo $i
        i=$(($i+1))
        sleep 1
done

echo "finish waiting for ElasticSearch!"

# 서버 실행
echo "executing server...!"
python3 app.py

echo "complete setting all the components :D"
