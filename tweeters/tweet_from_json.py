import json
from client import get_client

# Not to call this function everytime tweet method is called
tweeter_client = get_client()

class TweetJson:
    def __init__(self,filepath,paranoid=True):
        self.filepath = filepath # Unique source of data
        self.paranoid = paranoid

    def read_file(self):
        with open(self.filepath,"r") as file:
            file_content = file.read()
            statuses : list = json.loads(file_content)
            return statuses
    
    @property
    def get_untweeted_statuses(self):
        all_statuses = self.read_file()
        untweeted_statuses = filter(
                lambda status_object:status_object['tweeted'] == False,
                all_statuses
            )
        return list(untweeted_statuses)
        
    def tweet(self,status):
        response = tweeter_client.create_tweet(text=status['text'])
        return bool(response.data)
    
    def post_process(self,statuses=[],tweeted_statuses_ids=[]):
        """ Switch the tweeted property to True or delete the tweeted statuses from the .json file"""

        if self.paranoid:

            # Switch the tweeted property to True
            def mark_as_tweeted(status):
                if(status['id'] in tweeted_statuses_ids):
                    status['tweeted'] = True
                    return status
                else:
                    return status

            with_tweeted_statuses_marked_tweeted = list(map(
                mark_as_tweeted,
                statuses
            ))

            with open(self.filepath,'w') as file:
                file_content = json.dumps(
                    with_tweeted_statuses_marked_tweeted,
                    ensure_ascii=True
                )
                file.write(file_content)
                file.close()

        else:
            # Delete the tweeted statuses from the .json file
            def filter_statuses(status):
                return status['id'] not in tweeted_statuses_ids

            statuses_not_tweeted = list(filter(
                filter_statuses,
                statuses
            ))

            with open(self.filepath,'w') as file:
                file_content = json.dumps(
                    statuses_not_tweeted,
                    ensure_ascii=True
                )
                file.write(file_content)
                file.close()

    def run(self):
        """Loop through the filtered statuses and tweet them"""
        statuses_to_tweet = self.get_untweeted_statuses
        tweeted_statuses_ids = []

        for status in statuses_to_tweet:
            tweeted = self.tweet(status)
            tweeted_statuses_ids.append(status['id']) if tweeted else None

        # Now do the post processing i.e delete the tweeted statuses
        # or switch their tweeted property to True
        if len(tweeted_statuses_ids) >= 1 :
            self.post_process(
                statuses=statuses_to_tweet,
                tweeted_statuses_ids=tweeted_statuses_ids
            )   

# Test 
tweeter = TweetJson(filepath='news/source.json')
tweeter.run()

