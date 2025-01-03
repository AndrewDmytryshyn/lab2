import pika
import json
import time
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)

PROVIDER_ID = os.getenv("PROVIDER_ID", "1")

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

def callback(ch, method, properties, body):
    start_time = datetime.now()
    
    task = json.loads(body)
    logging.info(f"Provider {PROVIDER_ID} processing task: {task}")
    
    # Simulate processing time
    time.sleep(2)
    
    result = {
        'task_id': task.get('task_id'),
        'correlation_id': task.get('correlation_id'),
        'result': f"Processed by Provider {PROVIDER_ID}",
        'provider_id': PROVIDER_ID
    }
    
    # Send response back
    ch.basic_publish(
        exchange='',
        routing_key='response_queue',
        body=json.dumps(result),
        properties=pika.BasicProperties(
            correlation_id=properties.correlation_id
        )
    )
    
    ch.basic_ack(delivery_tag=method.delivery_tag)
    
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    logging.info(f"Provider {PROVIDER_ID} finished processing in {processing_time} seconds")

def main():
    wait_for_rabbitmq()
    
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    
    channel.queue_declare(queue='task_queue', arguments={
        'x-max-priority': 10
    })
    channel.queue_declare(queue='response_queue')
    
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='task_queue', on_message_callback=callback)
    
    logging.info(f" [*] Provider {PROVIDER_ID} waiting for tasks")
    channel.start_consuming()

if __name__ == "__main__":
    main()