
## Summarizer

This is the readme for the new summarizer application.

## How to Run it?


### Prerequisites.

Before running make sure you have Python and Docker Installed in Your machine.



### Download the Embedding Model.

Create a virtual environment and install transformer inside it.

Then run the following script to  download the embedding model locally.

`python scripts/download_model.py --model_name_or_path dunzhang/stella_en_400M_v5 --output_dir models`


## Generate Database credentials.

You need to connect to the database to download the news articles. 

`cp .env_sample .env_local`

Then reach out to me directly I will provide you with the credentials needed to run this application.


### Build the Docker Image.

After you have downloaded the embedding model, you can build the container using the following code.

` docker build -t espymur/summarization-clustering:latest -f docker/Dockerfile-base --build-arg PIP_SECTION=clustering-packages`


Run it with 
`docker run --env-file .env_local -v $(pwd)/models/dunzhang/stella_en_400M_v5:/home/code/models/dunzhang/stella_en_400M_v5 espymur/summarization-clustering:latest python  src/summarizer/main.py -e local -d 1`





