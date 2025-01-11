from typing import Dict, TypedDict, List, Literal
import os
from pathlib import Path
from dotenv import load_dotenv
import tweepy

class TweetDict(TypedDict):
    titles: List[str]
    urls: List[str]
    summary: str

class EnvironmentVars(TypedDict):
    consumer_secret : str | None
    consumer_key : str | None
    access_token : str | None
    access_token_secret : str | None
    bearer_token : str | None

ExecutionEnvType = Literal['local','production']

class TwitterClient:

    def load_environment_variables(self, environment: str = "local") -> EnvironmentVars:
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

        env_vars = {
            "consumer_secret": consumer_secret,
            "consumer_key" : consumer_key,
            "access_token" : access_token,
            "access_token_secret" : access_token_secret,
            "bearer_token" : bearer_token,
        }

        if None in env_vars.values():
            raise ValueError("There's an environnement variable missing !")
        
        return env_vars
    
    def init_client(self) -> tweepy.Client:
        """
            Instantiates the client to consume the API and returns it
        """

        env_vars = self.load_environment_variables()

        client = tweepy.Client(
            consumer_key=env_vars['consumer_key'],
            consumer_secret=env_vars['consumer_secret'],
            access_token=env_vars['access_token'],
            access_token_secret=env_vars['access_token_secret'],
            bearer_token=env_vars['bearer_token']
        )

        return client
    
    def __init__(self):

        env_vars = self.load_environment_variables()

        tweepy.OAuth1UserHandler(
            consumer_key=env_vars['consumer_key'],
            consumer_secret=env_vars['consumer_secret'],
            access_token=env_vars['access_token'],
            access_token_secret=env_vars['access_token_secret'],
        )

        self.client = self.init_client()

    def tweet(self,tweet:TweetDict,env:ExecutionEnvType):
        """
            Receives two arguments :

            tweet:TweetDict -> a dictionnary whose 'summary' property we will tweet
            env: str -> if env is equal to 'tweet', text will be printed to the command line.
        """
        if env == 'local':
            print(tweet)
            return True
        else:
            try :
                self.client.create_tweet(text=tweet['summary'])
                return True
            except Exception as error:
                return False

    def tweet_all(self,tweets:List[TweetDict],env:ExecutionEnvType):
        """
            Receives a list of dictionaries through which we loop to tweet each
        """
        for tweet in tweets:
            self.tweet(tweet,env)