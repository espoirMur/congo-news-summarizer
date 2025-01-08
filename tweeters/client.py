import os
import tweepy
from dotenv import load_dotenv
import sys

import tweepy.errors

load_dotenv()

# Read the env variables at once
consumer_key = os.getenv('TWITTER_CONSUMER_KEY')
consumer_secret = os.getenv('TWITTER_CONSUMER_SECRET')
access_token = os.getenv('TWITTER_ACCESS_TOKEN')
access_token_secret = os.getenv('TWITTER_ACCESS_SECRET')
bearer_token=os.getenv('TWITTER_BEARER_TOKEN')

# Authenticate the client
def authenticate():
    try:
        # auth = tweepy.OAuthHandler(consumer_key, consumer_secret) -> Deprecated since version 4.5
        # auth.set_access_token(access_token, access_secret) -> Deprecated since version 4.5

        auth = tweepy.OAuth1UserHandler(
            consumer_key,
            consumer_secret,
            access_token,
            access_token_secret,
        )

        return auth

    except tweepy.errors.Unauthorized as error:
        sys.stdout.write("Authentication failed, check your credentials validity !\n")
        sys.stdout.write(f"Error : {str(error)}\n")
        sys.exit(1)

    except tweepy.errors.Forbidden as error:
        sys.stdout.write("The request has been forbidden, retry later !\n")
        sys.stdout.write(f"Error : {str(error)}\n")
        sys.exit(1)

    except tweepy.errors.TooManyRequests as error:
        sys.stdout.write("Server overwhelmed, wait and retry !\n")
        sys.stdout.write(f"Error : {str(error)}\n")
        sys.exit(1)

        # Can we implement an algorithm that queues the tweets
        # and automatically retries later to post them ?


# Get the client to tweet
def get_client():
    authenticate()
    client = tweepy.Client(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
        bearer_token=bearer_token
    )

    return client
