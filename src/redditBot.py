#Authors: Christopher Geier, Jeffrey Yoo
#University of Virginia
#3/24/18

import requests
import json
import praw
import time
import boto3
import pandas as pd
import numpy as np



def avg_comment_sentiment(comment_list,client):
    '''
    MUST HANDLE TOP MODERATOR COMMENT BEFORE CALLING
    Params:
        List of comment objects
    Returns:
        Weighted average of comments
    '''
    comment_sentiment_list = []
    for comment in comment_list:
        response = client.detect_sentiment(
            Text=comment.body[0:299],
            LanguageCode='en'
        )
        global calls
        calls += 3
        if response['Sentiment']=='NEUTRAL':
            sentiment = 0
        elif response['Sentiment']=='POSITIVE':
            sentiment = 1
        elif response['Sentiment']=='NEGATIVE':
            sentiment = -1
        else:
            sentiment = 0
        comment_sentiment_list.append(comment.ups * sentiment)
    return sum(comment_sentiment_list) / len(comment_sentiment_list)

def avg_comment_brands(comment_list, client):
    ''' 
    Params:
        List of comment objects
    Returns:
        Weighted average of brand count
    '''
    comment_numbrands_list = []
    for comment in comment_list:
        response = client.detect_entities(
            Text=comment.body[0:299],
            LanguageCode='en'
        )
        global calls
        calls += 3
        organization_count = 0
        for ent in response['Entities']:
            if ent['Type'] == 'ORGANIZATION':
                #print(ent['Text'])
                organization_count += 1
        comment_numbrands_list.append(comment.ups * organization_count)
    return sum(comment_numbrands_list)/ len(comment_numbrands_list)

def title_sentiment(title, client):
    ''' 
    MUST HANDLE TOP MODERATOR COMMENT BEFORE CALLING
    Params:
        List of comment objects
    Returns:
        Weighted average of comments
    '''
    comment_sentiment_list = []
    response = client.detect_sentiment(
        Text=title[0:299],
        LanguageCode='en'
    )
    global calls
    calls += 3
    if response['Sentiment']=='NEUTRAL':
        sentiment = 0
    elif response['Sentiment']=='POSITIVE':
        sentiment = 1
    elif response['Sentiment']=='NEGATIVE':
        sentiment = -1
    else:
        sentiment = 0
    return sentiment

def title_brands(title, client):
    ''' 
    Params:
        List of comment objects
    Returns:
        Weighted average of brand count
    '''
    comment_numbrands_list = []
    response = client.detect_entities(
        Text=title[0:299],
        LanguageCode='en'
    )
    global calls
    calls += 3
    organization_count = 0
    for ent in response['Entities']:
        if ent['Type'] == 'ORGANIZATION':
            organization_count += 1
    return organization_count

def data_dict(submission, client):
    global reddit
    target_sub_ID=submission.id
    target_sub=reddit.submission(target_sub_ID)
    data_input={}
    data_input["Title Seniment"]=str(title_sentiment(target_sub.title, client))
    data_input["Title Brands"]=str(title_brands(target_sub.title, client))
    data_input["Author Link Karma"]=str(target_sub.author.link_karma)
    data_input["Author Comment Karma"]=str(target_sub.author.comment_karma)
    data_input["Author Age"]=str(((time.time()-target_sub.author.created_utc)/86400))
    commentList=[]
    target_sub.comments.replace_more(limit=0)
    i = 0
    for top_com in target_sub.comments:
        commentList.append(top_com)
        i += 1
        if i > 50:
            break
    data_input["Avg Comment Sentiment"]=str(avg_comment_sentiment(commentList, client))
    data_input["Avg Comment Brand Count"]=str(avg_comment_brands(commentList, client))
    global calls
    print(calls)
    return data_input

def api(post, client):
    URL = "https://2ut1lyn470.execute-api.us-east-1.amazonaws.com/beta"
    PARAMS = data_dict(post, client)
    r = requests.post(url = URL, data = json.dumps(PARAMS))
    data = r.json()
    return data




def main():#Creates Reddit Instance
	
	test_subreddit="scfb" #Our Test Subreddit

	#Takes in the file holding the ID of posts we have checked
	df = pd.read_csv("response_history.csv",names=['test'])
	response_hist_array=df['test']

	client = boto3.client('comprehend',
	                    aws_access_key_id='AKIAIRCW2LHVT4U52KGA',
	                    aws_secret_access_key='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')

	num_of_post=9
	for submission in reddit.subreddit(test_subreddit).top(limit=num_of_post):
	
		
		target_sub_ID=submission.id_from_url(submission.url)
		
		post_history_check=target_sub_ID in response_hist_array
		if(not post_history_check):
			target_sub=reddit.submission(target_sub_ID)
			test_result=api(target_sub,client)
			if(test_result['Prediction']['predictedLabel']=='1'):
				submission.reply("This post is a sponsored content.")
			else:
				submission.reply("This post is not a sponsored content.")
			response_hist_array=np.append(response_hist_array,[target_sub_ID])
			
	df.to_csv("response_history.csv", index=False)
	print("Program Finished")

reddit=praw.Reddit('bot1')
calls=0
main()