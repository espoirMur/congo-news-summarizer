## About tweet_from_json.py

The data fetched from the .json source file is assumed to be
a list of dict objects that contains, each, 3 key-value pairs:

```json
{
  "id": 128373828483888438,
  "text": "Stay tuned and get the latest news !",
  "tweeted": true
}
```

With :

- **id** being the timestamp of the moment the status was written to the file or any other unique identifier. This value is important for tracking or statistics sake.
- **text** being the actual text to post on X.
- **tweeted** being a boolean indicating wether this status has been tweeted already or is to be tweeted.

However, the choice if up the code consumer. When creating an instance of **TweetJson**, the choice is up to them to decide whether to completely delete tweeted statuses or add a tweeted tag on them (kind of paranoid deletion).

## Sample Json data

```json
[
  {
    "id": 12837382848334388438,
    "text": "We're trying to make a better world where everybody has access to true information !",
    "tweeted": true
  },
  {
    "id": 1283738243283888438,
    "text": "Proletarier aller lander vereinigt euch !",
    "tweeted": false
  },
  {
    "id": 10283373828483888438,
    "text": "Le Congo est grand et exige de nous de la grandeur !",
    "tweeted": false
  },
  {
    "id": 10283373828483488438,
    "text": "Un, deux, trois, ... Vietnams, tel est le mot d'ordre !",
    "tweeted": false
  },
  {
    "id": 102833749328483888438,
    "text": "Le président Tshisekedi dit qu'il ne construit par un barrage au Kasai à cause des abeilles !",
    "tweeted": false
  },
  {
    "id": 1028337243628483888438,
    "text": "Trent ans après, 2Pac Shakur retrouvé à Matanzas à Cuba alors qu'il allait acheter une bouteille de Rhum : il n'est jamais mort.",
    "tweeted": true
  }
]
```
