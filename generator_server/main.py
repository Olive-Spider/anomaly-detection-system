from fastapi import FastAPI
from random import uniform, randint
import time
import requests
import asyncio

app = FastAPI()

# Configuration parameters
DATA_FREQUENCY = 1  # Frequency of data generation in seconds
VALUE_RANGE = (40, 50)  # Range for normal values
ANOMALY_PROBABILITY = 0.1  # Probability of generating an outlier
ANOMALY_DETECTION_URL = "http://localhost:8000/detect"  # URL of the Anomaly Detection Server

async def generate_and_post_data():
    while True:
        value = uniform(*VALUE_RANGE)
        if randint(0, 100) < ANOMALY_PROBABILITY * 100:
            value += randint(10, 20)  # Introduce an outlier
        data_point = {
            "value": value,
            "timestamp": time.time()
        }
        try:
            response = requests.post(ANOMALY_DETECTION_URL, json=data_point)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed to post data to anomaly detection server: {e}")
        await asyncio.sleep(DATA_FREQUENCY)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(generate_and_post_data())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)