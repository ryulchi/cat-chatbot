from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI
import requests
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
global THREAD_ID

client = OpenAI(api_key=OPENAI_API_KEY)

# Define a request model for clearer API documentation and validation
class Query(BaseModel):
    question: str
    
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Initialize the Thread at the start of the app and store the thread_id
    thread = client.beta.threads.create()
    global THREAD_ID
    THREAD_ID = thread.id
    yield
    client.close()

app = FastAPI(lifespan=app_lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/ask/")
async def ask_catbot(query: Query):
    question = query.question.lower()
    message = client.beta.threads.messages.create(
        thread_id=THREAD_ID,
        role="user",
        content=question
    )
    run = client.beta.threads.runs.create_and_poll(
        thread_id=THREAD_ID,
        assistant_id=ASSISTANT_ID,
        instructions="The user has a premium account."
    )
    messages = client.beta.threads.messages.list(
        thread_id=THREAD_ID
    )
    print(messages)
    # Return the text part of the latest message which is from the assistant
    for message in reversed(messages):
        if message['role'] == 'assistant':
            return {'response': message['content']['text']}
    return {"response": "No response from the assistant."}

@app.get("/")
def read_root():
    # Return the static HTML file on the root URL
    return FileResponse("static/index.html")
