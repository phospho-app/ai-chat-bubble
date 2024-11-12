import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from models import QuestionOnUrlRequest
from typing import Dict, Optional
from urllib.parse import urlparse
from models import MainExecute
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

load_dotenv()

# Check that the environment variables are set
assert os.getenv("QDRANT_LOCATION"), "QDRANT_LOCATION environment variable not set"
assert os.getenv("QDRANT_API_KEY"), "QDRANT_API_KEY environment variable not set"
assert os.getenv("MISTRAL_API_KEY"), "MISTRAL_API_KEY environment variable not set"
assert os.getenv("URL"), "URL environment variable not set"
assert os.getenv(
    "DOMAIN_STATUS_FILE"
), "DOMAIN_STATUS_FILE environment variable not set"

URL = os.getenv("URL")
DOMAIN_STATUS_FILE = os.getenv("DOMAIN_STATUS_FILE")
DATA_FOLDER = "data"
ORIGINS = os.getenv("ORIGINS")
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8080")

host, port = urlparse(SERVER_URL).netloc.split(":")


# Dictionary to store the status of each domain
domain_status: Dict[str, str] = {}

# Dictionary to store MainExecute instances for each domain
domain_instances: Dict[str, MainExecute] = {}


def load_domain_status():
    if os.path.exists(DOMAIN_STATUS_FILE):
        with open(DOMAIN_STATUS_FILE, "r") as f:
            return json.load(f)
    else:
        return create_json_file()


def create_json_file():
    if os.path.exists(DATA_FOLDER):
        for filename in os.listdir(DATA_FOLDER):
            if filename.endswith(".json"):
                domain = filename[:-5]  # Remove the .json extension
                domain_status[domain] = "completed"
    save_domain_status()
    return domain_status


def save_domain_status():
    with open(DOMAIN_STATUS_FILE, "w") as f:
        json.dump(domain_status, f)


def initialize_domains():
    global domain_status, domain_instances
    domain_status = load_domain_status()
    print(f"Loaded domain status: {domain_status}")
    for domain, status in domain_status.items():
        print(f"Initializing domain: {domain}")
        if status == "completed":
            try:
                main_execute = MainExecute(domain, load=False)
                domain_instances[domain] = main_execute
            except Exception as e:
                logger.error(f"Failed to initialize domain {domain}: {str(e)}")
                domain_status[domain] = f"failed: {str(e)}"
                save_domain_status()


def submit_url(url: Optional[str]):
    if url is None:
        raise HTTPException(status_code=400, detail="URL not set")
    domain = urlparse(url).netloc
    if domain not in domain_status or domain_status[domain] not in [
        "queued",
        "processing",
        "completed",
    ]:
        domain_status[domain] = "queued"
        save_domain_status()
        logger.info(f"Submitting domain: {domain}")
        process_domain(domain)
        logger.info(f"{domain} indexation completed")
    else:
        logger.info(f"Domain {domain} already being processed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: You can add initialization code here
    logger.info("Starting the application")

    initialize_domains()

    logger.info(f"domains: {domain_status.keys()}")

    logger.info(f"URL: {URL}")

    logger.info(f"Server URL: {SERVER_URL}")

    yield  # Here the FastAPI application runs

    # Shutdown: You can add cleanup code here if needed
    print("Shutting down the application")


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS
    if ORIGINS is not None
    else [],  # Specifies the origins allowed to access this API
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (POST, GET, etc.)
    allow_headers=["*"],  # Allows all headers
)

app.mount("/component", StaticFiles(directory="component"), name="component")


def process_domain(domain: str):
    domain_folder = os.path.join("data", domain)
    os.makedirs(domain_folder, exist_ok=True)
    logger.info(f"Indexing domain: {domain}")
    try:
        domain_status[domain] = "processing"
        save_domain_status()
        main_execute = MainExecute(domain)
        domain_instances[domain] = main_execute
        domain_status[domain] = "completed"
        save_domain_status()
    except Exception as e:
        domain_status[domain] = f"failed: {str(e)}"
        save_domain_status()


@app.post("/question_on_url")
async def question_on_url(request: QuestionOnUrlRequest):
    if URL is None:
        raise HTTPException(status_code=400, detail="URL not set")
    url = URL
    logger.debug(f"Question on URL: {url}")
    question = request.question
    domain = urlparse(url).netloc

    logger.debug(f"Domain: {domain}")

    if domain not in domain_instances:
        raise HTTPException(status_code=400, detail="Domain not processed yet")

    if domain_status.get(domain) != "completed":
        raise HTTPException(status_code=400, detail="Domain processing not completed")

    logger.debug(f"Domains: {domain_instances.keys()}")
    main_execute = domain_instances[domain]

    return StreamingResponse(main_execute.ask(question), media_type="text/plain")


if __name__ == "__main__":
    initialize_domains()
    submit_url(URL)

    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(port), reload=True)
