## Design Document: Anomaly Detection System with Data Stream Generator

### Project Overview

The goal of this project is to develop an anomaly detection system that can identify unusual patterns in a data stream based on a moving average with deviation thresholding. This system is split into two main components:

1. **Data Generator Server**: Continuously generates simulated data that represents a real-time stream of metrics (e.g., financial transactions, system metrics, etc.).

2. **Anomaly Detection Server**: Consumes the data from the Data Generator Server, applies anomaly detection logic using a moving average-based approach, and flags any data points that exceed a specified threshold. When an anomaly is detected, the system logs the anomaly to a file.

This project will demonstrate skills in real-time data streaming, anomaly detection, and the use of FastAPI to build lightweight web servers.

---

### Functional Requirements

#### 1. Data Generator Server

The Data Generator Server is responsible for producing a simulated real-time data stream. This server should meet the following requirements:

1. **Data Generation**:
    - Generate floating-point values that represent a simulated metric. The values should be a mix of regular patterns (e.g., sinusoidal or linear trends) with random noise to resemble real-world scenarios.
    - Introduce periodic spikes or outliers to simulate potential anomalies.

2. **Data Posting**:
    - Post generated data points to the Anomaly Detection Server's `/detect` endpoint at regular intervals.

3. **Configuration**:
    - Allow configuration of parameters such as the frequency of data generation, the range of normal values, and the probability of generating an outlier.

#### 2. Anomaly Detection Server

The Anomaly Detection Server consumes data from the Data Generator Server and applies an anomaly detection algorithm. This server should meet the following requirements:

1. **Data Ingestion**:
    - Receive data points via POST requests to the `/detect` endpoint.

2. **Anomaly Detection Logic**:
    - Implement a **Moving Average with Deviation Thresholding** algorithm:
        - Calculate a moving average and standard deviation over a sliding window of recent data points.
        - Define a threshold as the moving average plus a multiple (configurable) of the standard deviation.
        - If a data point exceeds this threshold, it is considered an anomaly.
    - The moving window size and threshold multiplier should be configurable.

3. **Anomaly Logging**:
    - Upon detecting an anomaly, log the anomaly data to a specified file.

4. **Endpoints**:
    - `/detect`: Receives data points from the generator, applies anomaly detection, and logs anomalies if detected.
        - **Method**: POST
        - **Response**: JSON indicating the status of data processing (e.g., `{ "status": "Data received and processed" }`).
    - `/anomalies`: Retrieves recent anomalies for reporting purposes (optional, can be expanded to store historical anomalies).
        - **Method**: GET
        - **Response**: JSON list of recent anomalies (if stored).

5. **Error Handling and Logging**:
    - Implement robust error handling to manage data receive failures, threshold calculation issues, and file logging errors.
    - Log all detected anomalies and any errors during detection.

---

### Technical Design

#### Architecture Overview

The system consists of two independent services, both built using FastAPI:

- **Data Generator Server**: Generates synthetic data and posts it to the Anomaly Detection Server.
- **Anomaly Detection Server**: Receives data, detects anomalies, and logs them to a file.

#### Algorithm

1. **Moving Average with Deviation Thresholding**:
    - Calculate a moving average and standard deviation over a sliding window of the last N data points.
    - Define an anomaly as any data point that exceeds the moving average plus a configurable multiplier of the standard deviation.
    - The moving average window size (N) and deviation multiplier are parameters that should be adjusted to balance detection sensitivity and minimize false positives.

#### API Specification

1. **Data Generator Server**
    - **Configuration Parameters**:
        - `data_frequency`: How often new data points are generated (e.g., every second).
        - `value_range`: Range for normal values (e.g., 40 to 50).
        - `anomaly_probability`: Probability of generating an outlier.
        - `anomaly_detection_url`: URL of the Anomaly Detection Server's `/detect` endpoint.

2. **Anomaly Detection Server**
    - **Endpoints**:
        - `/detect`
            - **Method**: POST
            - **Description**: Receives data points from the generator, applies anomaly detection, and logs anomalies if detected.
            - **Response**:
              ```json
              {
                "status": "Data received and processed"
              }
              ```
        - `/anomalies`
            - **Method**: GET
            - **Description**: Retrieves recent anomalies.
            - **Response**:
              ```json
              [
                {
                  "value": 100.5,
                  "timestamp": 1698401060.0,
                  "mean": 45.0,
                  "std_dev": 2.5
                }
              ]
              ```
    - **Configuration Parameters**:
        - `window_size`: Number of recent data points to calculate the moving average.
        - `threshold_multiplier`: Multiplier of the standard deviation used to determine if a point is anomalous.
        - `anomaly_log_file`: File to log anomalies.

---

### Example Code

#### 1. Data Generator Server

```python
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
ANOMALY_DETECTION_URL = "http://localhost:8001/detect"  # URL of the Anomaly Detection Server

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
```

### To Run Project
### Begin by running both servers
### On Windows:
anomaly_server:
	cd anomaly_server
	python -m uvicorn main:app --reload

generator_server:
	cd generator_server
	python -m uvicorn main:app --port 8080 --reload

### On Mac/Linux
anomaly_server:
	cd anomaly_server && uvicorn main:app --reload

generator_server:
	cd generator_server && uvicorn main:app --port 8080 --reload

#### Run your HTML server
Run front-end/index.html for visualization.
