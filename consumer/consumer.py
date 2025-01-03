import pika
import json
import time
import logging
import os
from fastapi import FastAPI
import uvicorn
from datetime import datetime

app = FastAPI()
logging.basicConfig(level=logging.INFO)

CONSUMER_ID = os.getenv("CONSUMER_ID", "1")

def wait_for_rabbitmq():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host='rabbitmq'))
            connection.close()
            break
        except pika.exceptions.AMQPConnectionError:
            logging.info("Waiting for RabbitMQ...")
            time.sleep(5)

class MessageBroker:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rabbitmq'))
        self.channel = self.connection.channel()
        
        # Declare queues with priorities
        self.channel.queue_declare(queue='task_queue', arguments={
            'x-max-priority': 10
        })
        self.channel.queue_declare(queue='response_queue')

broker = None

@app.post("/process")
async def process_task(task: dict):
    global broker
    if broker is None:
        broker = MessageBroker()
    
    start_time = datetime.now()
    
    # Add correlation ID for request-reply pattern
    correlation_id = str(time.time())
    task['correlation_id'] = correlation_id
    task['priority'] = task.get('priority', 5)  # Default priority
    
    # Log request time
    logging.info(f"Consumer {CONSUMER_ID} processing request at {start_time}")
    
    # Publish to task queue
    broker.channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=json.dumps(task),
        properties=pika.BasicProperties(
            priority=task['priority'],
            correlation_id=correlation_id
        )
    )
    
    # Wait for response
    result = {'status': 'processing'}
    
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    logging.info(f"Consumer {CONSUMER_ID} finished processing in {processing_time} seconds")
    
    return result

if __name__ == "__main__":
    wait_for_rabbitmq()
    uvicorn.run(app, host="0.0.0.0", port=8000)