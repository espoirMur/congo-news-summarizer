


### Build the Docker Image.

` docker build -t espymur/summarization:dev -f deployment/docker-files/Dockerfile-base --build-arg PIP_SECTION=news-summarizer --build-arg COMPONENT_NAME=summarizer --build-arg COMPONENT_PATH=src/summarizer .`


Run it with 
`docker run -v $(pwd)/src:/app/src --env-file .env_prod espymur/summarization:dev python src/summarizer/main.py -e prod -st b2 -d 7`




## Before installing the model

Run the following script to install the model.

`python scripts/download_model.py --model_name_or_path dunzhang/stella_en_400M_v5 --output_dir models`


Make sure you have the transformer model installed in the application
