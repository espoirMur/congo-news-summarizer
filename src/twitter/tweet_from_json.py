import json
from twitter_client import TwitterClient

class TweetJson:
    def __init__(self):
        self.client_twitter = TwitterClient()

    def tweet(self,status):
        response = self.client_twitter.tweet(text=status['summary'])
        return bool(response.data)
    
    def run(self,statuses_to_tweet):
        for status in statuses_to_tweet:
            self.tweet(status)

