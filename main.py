from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import requests

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
assistant = client.beta.assistants.create(
    instructions="You are a cat chatbot. You can answer questions about cats and provide cat images with the function.",
    model="gpt-3.5-turbo-16k",
    tools=[{
        "type": "function",  # Ensure 'type' is correctly set based on the API documentation
        "function": {        
            "name": "get_cat_image",
            "description": "Returns a cat image from CatAPI.",
            "parameters": {},
            "returns": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "url": {"type": "string"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                    "breeds": {"type": "array"},
                    "favourite": {"type": "object"}
                }
            }
        }
    }]
)

thread = client.beta.threads.create()

class Query(BaseModel):
    question: str

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/ask/")
async def ask_catbot(query: Query):
    user_input = query.question.lower()
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )
    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        for m in reversed(messages.data):
            if m.role == 'assistant':
                return {"answer": m.content[0].text.value}
    elif run.status == 'failed':
        return {"answer": "Run failed due to: {}".format(run.last_error)}
    elif run.status == 'requires_action':
        tool_outputs = []
        for tool in run.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name == "fetch_cat_image":
                tool_outputs.append({
                    "tool_call_id": tool.id,
                    "output": requests.get("https://api.thecatapi.com/v1/images/search")                
                })
        if tool_outputs:
            try:
                run = client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
            except Exception as e:
                return {"answer": "Run failed due to:" + e}
        if run.status == 'completed':
            messages = client.beta.threads.messages.list(
                thread_id=thread.id
            )
            for m in reversed(messages.data):
                if m.role == 'assistant':
                    return {"answer": m.content[0].text.value}
        else:
            return {"answer": "Run failed due to: {}".format(run.last_error)}

@app.get("/")
def read_root():
    return FileResponse("static/index.html")