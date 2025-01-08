from client import get_client

# Tweet 
def tweet(status:str):
    client = get_client()
    response = client.create_tweet(text=status)
    return response


# Test 
tweet('Stay tuned and get the latest infos !')