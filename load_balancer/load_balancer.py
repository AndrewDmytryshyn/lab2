from fastapi import FastAPI
import httpx
import random
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)

CONSUMERS = ["consumer1:8000", "consumer2:8000"]

@app.post("/task")
async def handle_task(task: dict):
    consumer = random.choice(CONSUMERS)
    logging.info(f"Forwarding request to consumer: {consumer}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"http://{consumer}/process", json=task)
        return response.json()