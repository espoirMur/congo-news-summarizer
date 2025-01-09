from typing import Tuple, Dict, List
import os
from pathlib import Path
from dotenv import load_dotenv
import tweepy

class TwitterClient:

    def load_environment_variables(self, environment: str = "local") -> Tuple[str, str]:
        """Load an environment variables and return them, raise a value error if one of them is empty."""

        # Get a specific ENV file
        current_directory = Path.cwd()
        env_file = current_directory.joinpath(f".env_{environment}")
        load_dotenv(env_file)

        # Load the variables
        consumer_key = os.getenv('TWITTER_CONSUMER_KEY')
        consumer_secret = os.getenv('TWITTER_CONSUMER_SECRET')
        access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        access_token_secret = os.getenv('TWITTER_ACCESS_SECRET')
        bearer_token=os.getenv('TWITTER_BEARER_TOKEN')

        env_vars = (
            consumer_secret,
            consumer_key,
            access_token,
            access_token_secret,
            bearer_token,
        )

        if None in env_vars:
            raise ValueError("There's an environnement variable missing !")
        
        return env_vars
    
    def init_client(self):

        consumer_key,consumer_secret,access_token,access_token_secret, bearer_token, = self.load_environment_variables()

        client = tweepy.Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            bearer_token=bearer_token
        )

        return client
    
    def __init__(self):

        consumer_key,consumer_secret,access_token,access_token_secret,bearer_token = self.load_environment_variables()

        self.auth = tweepy.OAuth1UserHandler(
            consumer_key,
            consumer_secret,
            access_token,
            access_token_secret,
        )

        self.client = self.init_client()

    def tweet(self,text:str,env:str):
        if env == 'tweet':
            print(text)
        else:
            self.client.create_tweet(text)

    def tweet_all(self,tweets:list):
        for tweet in tweets:
            self.client.create_tweet(text=tweet['summary'])