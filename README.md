# AI chat bubble - custom AI assistant connected to your knowledge

**Simple and fast AI chat bubble for your HTML website.** The AI assistant can answer questions about a website's content using RAG, streaming, and the Mistral model. Compatible with **React** and **Wordpress**!

**How does it work ?**

1. Run the backend to create an assistant with knowledge about your website's content
2. Add a code snippet to your HTML frontend
3. Your users can now chat with an assistant in an AI chat bubble!

**Production-ready**

You can host the AI chat bubble on your own machine with a simple `docker-compose up --build`.
See what users are asking thanks to [phospho analytics](https://phospho.ai) already integrated.

![ai chat bubble](https://github.com/user-attachments/assets/32a5172a-017e-41ac-a59b-c9940e541380)

## Quickstart

### 1. Setup .env

Clone this repository.

```bash
# clone using the web url
git clone https://github.com/phospho-app/ai-chat-bubble.git
```

Then, create a `.env` file at the root with this content:

```bash
URL=https://www.example.com # Your assistant will know everything about this URL

# To add:
MISTRAL_API_KEY=...
PHOSPHO_API_KEY=...
PHOSPHO_PROJECT_ID=...
```

In `URL`, put the website with the relevant content you want the AI assistant to know about.
The assistant will crawl domains with a depth of 3 (this is customizable).

#### External services

- **LLM:** We use the Mistral AI model - _mistral-large-latest_. Get your `MISTRAL_API_KEY` [here](https://mistral.ai).
- **Analytics:** Messages are logged to phospho. Get your `PHOSPHO_API_KEY` and your `PHOSPHO_PROJECT_ID` [here](https://platform.phospho.ai).

### 2. Run the assistant backend

To deploy the backend of the AI chat bubble, this repository uses [docker compose](https://docs.docker.com/compose/). [Follow this guide to install docker compose](https://docs.docker.com/compose/install/), then run the assistant's backend:

```bash
cd ai-chat-bubble # the name of the clone repo
docker-compose up --build
```

Questions are sent to the assistant using the POST API endpoint `/question_on_url`. This returns a streamable response. Go to [localhost:8080/docs](localhost:8080/docs) for more details.

### 3. Add the chat bubble to your website

Add the chat bubble to your website with this snippet in a HTML component:

```html
<script src="http://localhost:8080/component/chat-bubble.js" async></script>
```

If you just wan to test your assistant, you simply need to open the `demo.html` file in your browser.

Look into advanced configuration to change its style.

## Advanced configuration

### Change the chat bubble UI

The file `component/chat-bubble.js` contains the AI chat bubble style. It is served as a static file and is the compiled version of `interface/chat-bubble.js`.

To change the AI chat bubble, edit the `interface/chat-bubble.js` and then run `npx webpack` in the folder _app_ of the repo.

### CORS policy

In production, it's best to setup a restrictive CORS policy to allow only your frontend to call your AI assistant backend. To do this, add an `ORIGINS` list in your `.env`.

```
ORIGINS = ["http://localhost:3000", "http://localhost:3001"]
```

_Only urls in `ORIGINS` can access the `/question_on_url` endpoint._

### Edit ports

The docker runs the main app on port _8080_. To change it, add a `SERVER_URL` field in your `.env`.

```
SERVER_URL=your_new_port
```

Then change the source of the interface script: `<script src="your_new_port/component/chat-bubble.js" async />`

### Prompts, AI, vector databases

The AI assistant of the AI chat bubble uses [Llama Index](https://docs.llamaindex.ai/en/stable/), [Qdrant](https://qdrant.tech/documentation/), and [Mistral](https://docs.mistral.ai). This behaviour is implemented in `models.py`.

- Edit `ChatMistral` to change the prompts or models
- Edit the `EmbeddingsVS` client to use another Vector store than Qdrant

## About

Made by juniors for juniors in PARIS - phospho team 🥖🇫🇷

Special thanks to @flamschou, @fred3105, and @oulianov 🧪💚
