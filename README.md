# One click custom domain assistant expert

This repository implements an assistant chatbot that proceed RAG on a custom website.

**How it works ?**

The assistant gets information from an url you gave, store the embeddings in a vector database and use a LLM to generate answers.

## Set up

After cloning the repository, put the following informations in your `.env`.

```python
URL="https://www.example.com"

MISTRAL_API_KEY="your_mistral_api_key"

QDRANT_API_KEY="your_qdrant_api_key"
QDRANT_LOCATION="your_qdrant_location"

DOMAIN_STATUS_FILE="domain_status.json"
```

In `URL` put the url you want the assistant to know about.
The assistant will crawl domains with a depth of 3 (this is customizable).

_Keep the `DOMAIN_STATUS_FILE` as it is._

### QDRANT

The assistant stores the embeddings of the pages it visited in the vector database QDrant. [Create an account](https://qdrant.tech), a cluster and get your `QDRANT_URL_KEY`and your `QDRANT_LOCATION`. For one webpage, the free tiers should be more than enough.

### MISTRAL

The assistant needs an LLM to generate an answer. Here, a Mistral ai model is used - _mistral-large-latest_, so you need a `MISTRAL_API_KEY`. You can [obtain one here](https://mistral.ai).

## Run the assistant

You can launch the assistant from a python3.11 environment.

```bash
cd clone_repo_path
pip install poetry
poetry install
python main.py
```

This repository contains a **Docker** file, so you can run the assistant using a docker daemon.

```bash
cd clone_repo_path
docker build -t chatbot .
docker run --env-file .env -p 8080:8080 chatbot
```

I choose to name my docker image _chatbot_ and to run it on port _8080_. Feel free to change that, it will not affect how the assistant works.

If you change the port, make sure you change it in the `.env`, `SERVER_URL`

## Communicate to the assistant

Now you can send questions to the assistant using the POST API endpoint `/question_on_url`. It will return streamable response. If you want to call it from an other virtual machine, add it to the `ORIGINS`list in your `.env`.

Example:

```
ORIGINS = ["http://localhost:3000", "http://localhost:3001"]
```

_Only urls in `ORIGINS` can access the `/question_on_url` endpoint._

## Integrate it in your site

You can easily add an assistant interface by adding `<script src="http://localhost:8080/component/chat-bubble.js" async />` in a HTML component.

_If you changed the port of the assistant, change iy also in `.env`._

The file `component/chat-bubble.js` is served as a static file and is the compiled version of the `interface/chat-bubble.js`. To change it, modify the `interface/chat-bubble.js` and then run `npx webpack` in the root of the repo.
