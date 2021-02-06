from flask import Flask, render_template, request
import tweepy
import re
from textblob import TextBlob
import bs4
import requests
import json
from langdetect import detect

app = Flask(__name__)

@app.route('/')
def home():
	return render_template('index.html')

@app.route('/Twitter')
def Twitter():
	return render_template('Twitter.html')	

@app.route('/Instagram')
def Instagram():
	return render_template('Instagram.html')		

@app.route('/Twitter_Opinion_Mining', methods = ['POST', 'GET'])
def Twitter_Opinion_Mining():

	consumer_key = "gzagmEkiehIpkL7PwFPj5QQji"
	consumer_secret = "deezNCKQbs3wEaXlc3YU8Q9LIee1JQQJohbVsKqhDJ4WAGdRnY"
	access_token = "1320296533556772864-G14nDY0KtPDcKfynIpuDV6XUNA0dca" 
	access_token_secret = "q02xnTWk68MxfaY2vPUKZ1GpP5dyjc6aQ9E4bULJKOOHp"

	method = int(request.form['Option'])
	query = request.form['ScreenName']
	Count = request.form['Count']

	for c in Count :
		if c<'0' or c>'9':
			return render_template('Twitter.html', error=0) 	

	if int(Count)>200:
		Count="200"

	try:
		auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
		auth.set_access_token(access_token, access_token_secret)
		api = tweepy.API(auth)

	except:
		return "Error : Authentication Failed !!!"

	full_tweets = []

	if method==1:
		tweets = api.user_timeline(screen_name= query, count= Count, lang="en", tweet_mode="extended")

	else:
		tweets = api.search(q = query, count = Count, lang="en", tweet_mode="extended")

	for tweet in tweets:
		try:
			full_tweets.append(tweet.retweeted_status.full_text)
		except:
			full_tweets.append(tweet.full_text)	


	if len(full_tweets)==0 :
		return render_template('Twitter.html', error=1)

	positive_tweets = []
	negative_tweets = []
	neutral_tweets = []

	for tweet in full_tweets:
		raw_tweet = tweet
		raw_tweet = re.sub("@[A-Za-z0-9_]+", " ", raw_tweet) # remove mentions
		raw_tweet = re.sub(r"https?:\/\/\S+", " ", raw_tweet) # remove hyper links
		raw_tweet = re.sub(r"#[A-Za-z0-9_]+", " ", raw_tweet) # remove hashtags
		raw_tweet = re.sub(r"[^A-Za-z0-9 \t]", " ", raw_tweet) # remove non alphanumeric characters
		raw_tweet = re.sub(r"RT", " ", raw_tweet) # remove RT

		if raw_tweet.strip() == "":
			neutral_tweets.append(tweet)
			continue

		tweet_polarity = TextBlob(raw_tweet).sentiment.polarity
		if tweet_polarity > 0:
			positive_tweets.append(tweet)

		elif tweet_polarity < 0:
			negative_tweets.append(tweet)

		else:
			neutral_tweets.append(tweet)		

	user = {'pos': len(positive_tweets), 'neg': len(negative_tweets), 'neu': len(neutral_tweets)}
	return render_template('tweets.html', timeline_tweets = full_tweets, pos_tweets = positive_tweets, 
	neg_tweets = negative_tweets, neut_tweets = neutral_tweets, user = user)	

@app.route('/Insta_Opinion_Mining', methods = ['POST', 'GET'])
def Insta_Opinion_Mining():
	
	query = request.form['Hashtag']
	pos = []
	neg = []
	neu = []
	posts = []

	url_string = "https://www.instagram.com/explore/tags/%s/" % query
	response = bs4.BeautifulSoup(requests.get(url_string).text, "html.parser")
	
	for script_tag in response.find_all("script"):
		if script_tag.text.startswith("window._sharedData ="):
			shared_data = re.sub(r"window\._sharedData = ", "", script_tag.text)
			shared_data = re.sub(";$", "", shared_data)
			shared_data = json.loads(shared_data)

	if 'HttpErrorPage' in shared_data['entry_data']:
		return render_template('Instagram.html', error=0)
		
	try:
		media = shared_data['entry_data']['TagPage'][0]['graphql']['hashtag']['edge_hashtag_to_media']['edges']
		for nd in media:
			tag = nd['node']['edge_media_to_caption']['edges'][0]['node']['text']
        
			try: 
				if detect(tag)=='en' and tag not in posts:
					posts.append(tag)
					
			except:
				pass

	except:	
		return render_template('captions.html', posts = posts, pos = pos, neg = neg, neu = neu)	

	for tag in posts:
		post = tag
		post = re.sub(r"#[A-Za-z0-9]+", " ", post)
		post = re.sub("@[A-Za-z0-9]+", " ", post)
		post = re.sub(r"[^0-9A-Za-z \t]", " ", post)
		post = re.sub(r"\w+:\/\/\S+", " ", post)
		post = re.sub(r"\s+"," ", post) 	

		if post.strip()=="" :
			neu.append(tag)
			continue

		caption_polarity = TextBlob(post).sentiment.polarity
		if caption_polarity > 0:
			pos.append(tag)

		elif caption_polarity < 0:
			neg.append(tag)

		else:
			neu.append(tag)		

	user = {'pos': len(pos), 'neg': len(neg), 'neu': len(neu)}
	return render_template('captions.html', posts = posts, pos = pos, neg = neg, neu = neu, user = user)			

if __name__ == "__main__":
	app.config['SESSION_COOKIE_SECURE'] = False
	app.run(debug = True)