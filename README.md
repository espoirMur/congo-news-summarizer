## Congo News Summarizer


Over the past months, I have been collecting a lot of news articles from major Congolese news websites. I have those articles saved in a Postgres database. There is a lot of fun stuff I can do with them. Among them is a news summarizer. I want to analyze the daily news and find out what the websites are talking about.

In this project, I will try to build that news summarizer.


## Architecture

The summarizer has 3 main components.

A new collector,  cluster model and a Generative model.

### New Collector

This is build with scrappy scrappers, they scrape the news website and download the news data.

### The cluster model

This is a machine learning model that pulls today news and runs a hierarchical clustering model on them. The output of this a a dataframe with news clusters. You can learn more on how I have implemented the clustering [here](./notebooks/new-summarizer-clustering.ipynb).


### A generative model.

This component, start from the output of the clustering model and build a summary for each new cluster.

It use a self hosted Language model to generate the summary of the news.  I am working on a blog post that document all the process of building the generative model.

### Technologies:

The Generative model is hosted using llama.cpp and run on ubuntu VPS for inference.


### A front end

This is the final part, it will display the news summaries as a UI and user can interact with it.


### 

