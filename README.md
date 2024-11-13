# AI chat bubble - custom AI assistant connected to your knowledge

Add an AI chat bubble to your website in no time. The AI assistant can answer questions about a website's content using **RAG**, streaming, and the Mistral model. 

```bash
# Example: Create a chatbot that can answer question about https://docs.phospho.ai 
URL="https://docs.phospho.ai" docker-compose up --build
```

```html
// Add the chatbubble to your frontend
<script src="component/chat-bubble.js" async />
```

Result: 

<!--![Assistant closed](images/assistant_closed.png)-->

![Chat with assistant](images/chat_with_assistant.png)

**How does it work ?**

1. Add a code snippet to your frontend
2. Connect a URL to give knowledge to your assistant
3. Answer your users' questions with RAG
4. Analyze conversations to improve the knowledge

## 1. Set up .env

After cloning the repository, create a `.env` file at the root of the repository with the following content:

```bash
URL="https://www.example.com" # Your assistant will know everything about this URL

MISTRAL_API_KEY="your_mistral_api_key" 
ORIGINS=["*"] # Used for CORS policy
PHOSPHO_API_KEY="your_phospho_api_key"
PHOSPHO_PROJECT_ID="you_phospho_project_id"
DOMAIN_STATUS_FILE="domain_status.json"
```

In `URL`, put the website with the relevant content you want the assistant to know about.
The assistant will crawl domains with a depth of 3 (this is customizable).

_Note: Keep the `DOMAIN_STATUS_FILE` as it is._

### External services

- **LLM:** We use the Mistral AI model - _mistral-large-latest_, so you need a `MISTRAL_API_KEY`. [Get one here](https://mistral.ai).
- **Analytics:** Messages are logged to phospho. Get your `PHOSPHO_API_KEY` and your `PHOSPHO_PROJECT_ID` [here](https://platform.phospho.ai).

## 2. Run the assistant backend

This repository contains a **docker-compose.yml** file. Run the assistant's backend this way:

```bash
cd clone_repo_path
docker-compose up --build
```

Questions are sent to the assistant using the POST API endpoint `/question_on_url`. This returns a streamable response. 

## 3. Add the chat bubble to your website

Add the chat bubble to your website using this code snippet in a HTML component:

```html
<script src="http://localhost:8080/component/chat-bubble.js" async />
```

## Advanced setup

### Ports

The docker runs the main app on port _8080_. To change it, add a `SERVER_URL` field in your `.env`.

```
SERVER_URL=your_new_port
```

Then change the source of the interface script: `<script src="your_new_port/component/chat-bubble.js" async />`

### Change the chat bubble UI

The file `component/chat-bubble.js` is served as a static file and is the compiled version of `interface/chat-bubble.js`. 

To change it, edit the `interface/chat-bubble.js` and then run `npx webpack` in the folder _app_ of the repo.

### CORS policy

In production, it's best to setup a more restrictive CORS policy. For example, to allow only your frontend to call your assistant. To do this, change the `ORIGINS` list in your `.env`.

```
ORIGINS = ["http://localhost:3000", "http://localhost:3001"]
```

_Only urls in `ORIGINS` can access the `/question_on_url` endpoint._
