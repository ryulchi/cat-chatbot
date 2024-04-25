from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI
import requests
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

class Query(BaseModel):
    question: str

@app.post("/ask/")
async def ask_catbot(query: Query):
    question = query.question.lower()
    breeds = ['pers', 'siam', 'abys', 'beng', 'sphy', 'ragd', 'sibe']
    if "cat" in question:
        for breed in breeds:
            if breed in question:
                url = "https://api.thecatapi.com/v1/images/search?limit=1&breed_ids={}".format(breed)
                cat_response = requests.get(url)
                cat_image_url = cat_response.json()[0]['url']
                return {"answer": f"<img src='{cat_image_url}' alt='Cat'/>"}        
        cat_response = requests.get("https://api.thecatapi.com/v1/images/search")
        cat_image_url = cat_response.json()[0]['url']
        return {"answer": f"<img src='{cat_image_url}' alt='Cat'/>"}
    return {"answer": "I'm sorry, I can only answer questions about cats."}

@app.get("/")
def read_root():
    return FileResponse("static/index.html")