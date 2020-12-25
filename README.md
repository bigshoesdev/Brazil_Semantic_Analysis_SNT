# scopo_deep

## Overview

Scopo_deep is a Scrapping, Deep Learning engine to analyze data and deliver the result to the SCOPO Online system.
The Scopo_deep backend is currently powered by 2 microservices, all of which happen to be written in Python.

* Scrapping Engine by Daemon: scrapes text json from Facebook, Twitter, Instagram and Politicios and saves them to MongoDB
* Restful API Service: Provides all data by API

## 1. Scraping

Make sure you've got python 3 or greater and pip installed, then hit

```bash
# install dependencies

- Install Python 3, git, git-lfs.
- Run `pip install -r requirements.txt`
- Run `./rest_server.py` to start the server
```

In order to run the scraping script in terminal, please use the following commands:

```bash
python scrapy.py -t facebook -k post -p RogerioLisboaOFICIAL --since=2017-01-01 --until=2020-04-14
python scrapy.py -t facebook -k post -p RogerioLisboaOFICIAL
python scrapy.py -t facebook -k comment -p RogerioLisboaOFICIAL
python scrapy.py -t twitter -u jairbolsonaro --since=2017-01-01 --until=2020-04-14
python scrapy.py -t twitter -u jairbolsonaro
python scrapy.py -t twitter -u jairbolsonaro --since=2017-01-01
```

## 2. Topic Modeling
**Topic Modeling Training**
```
python -m topic_modeling.tm_tokenize -t twitter -u RogerioMLisboa
python -m topic_modeling.tm_tokenize -t facebook -u RogerioLisboaOFICIAL
python -m topic_modeling.tm_tokenize -t facebook -u 540506462807627

python -m topic_modeling.tm_lda -t twitter -u RogerioMLisboa
python -m topic_modeling.tm_lda -t facebook -u RogerioLisboaOFICIAL
python -m topic_modeling.tm_lda -t facebook -u 540506462807627

python -m topic_modeling.tm_run -t twitter -u RogerioMLisboa
python -m topic_modeling.tm_run -t facebook -u 540506462807627
```

Topic modeling deliver the result to show the percent of like and dislike per candidate per SNS (facebook, twitter).

### Request & Response API

**URL:**
```
 topic_modeling/api/v1.0/posts
```
**Method:**
```
 GET
```
**Data Param:**
```
{
  "name": [string],
  "type": [string]
}
```
**Example:**
```
  http://sm.scopo.online/topic_modeling/api/v1.0/posts?name=RogerioMLisboa&type=twitter
```
**Success Response:**
```
<html>
    <body>
        <link rel="stylesheet" type="text/css" href="https://cdn.rawgit.com/bmabey/pyLDAvis/files/ldavis.v1.0.0.css">
        <div id="ldavis_el168021405891250932005386773552"></div>
        <script type="text/javascript">

... ...

}else{
    // require.js not available: dynamically load d3 & LDAvis
    LDAvis_load_lib("https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.5/d3.min.js", function(){
         LDAvis_load_lib("https://cdn.rawgit.com/bmabey/pyLDAvis/files/ldavis.v1.0.0.js", function(){
                 new LDAvis("#" + "ldavis_el168021405891250932005386773552", ldavis_el168021405891250932005386773552_data);
            })
         });
}
</script>
    </body>
</html>
```
**Error Response:**
```
{
  "status": 404,
  "error": {
      "message": "The candidate name is not valid"
  }
}
```

## 3. Sentiment analysis
```
python -m sentiment_analysis.preprocess
python -m sentiment_analysis.train_pos_neg_neu
python -m sentiment_analysis.eval_pos_neg_neu --eval_train

python -m sentiment_analysis.train_pos_neg
python -m sentiment_analysis.eval_pos_neg --eval_train
python -m sentiment_analysis.eval_pos_neg_api
```

### Request & Response API

**URL:**
```
 sentiment/api/v1.0/posts
```
**Method:**
```
 POST
```
**Data Param:**
```
{
  "name": [string],
  "type": [string]
}
```
**Example:**
```
{
  "name": "BetoRicha",
  "type": "twitter"
}
```
**Success Response:**
```
{
  "status": 200,
  "response": {
      "likes": 68.4,
      "hates": 31.6
  }
}
```
**Error Response:**
```
{
  "status": 404,
  "error": {
      "message": "The candidate name is not valid"
  }
}
```

## 4. Word Cloud Tag Modeling
**Word Cloud Tag Modeling Training**
```
python -m topic_modeling.twitter_tagcloud -t twitter -u RogerioMLisboa
```

Word Cloud Tag modeling deliver the result to show pull out the most pertinent parts of textual data, from blog posts to databases per candidate per SNS (facebook, twitter).

### Request & Response API

**URL:**
```
 tag_modeling/api/v1.0/posts
```
**Method:**
```
 GET
```
**Data Param:**
```
{
  "name": [string],
  "type": [string]
}
```
**Example:**
```
  http://sm.scopo.online/tag_modeling/api/v1.0/posts?name=RogerioMLisboa&type=twitter
```
**Success Response:**
```
Word Tag Cloud Image
```
**Error Response:**
```
{
  "status": 404,
  "error": {
      "message": "The candidate name is not valid"
  }
}
```


**Celery Run On Localhost**
```
celery -A rest_server.celery worker --loglevel=info -P eventlet
celery -A rest_server.celery beat
http://localhost:15672/#/
```



