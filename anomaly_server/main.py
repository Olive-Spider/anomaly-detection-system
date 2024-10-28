import logging
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import statistics

app = FastAPI()

# Add CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration parameters
WINDOW_SIZE = 10  # Number of recent data points to calculate the moving average
THRESHOLD_MULTIPLIER = 2  # Multiplier of the standard deviation used to determine if a point is anomalous
ANOMALY_LOG_FILE = "anomalies.log"  # File to log anomalies
DATA_LOG_FILE = "data.log"  # File to log data points

# Initialize variables
recent_data = []
anomalies = []

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KeyEncoder(json.JSONEncoder):
    def _iterencode(self, o, markers=None):
        return super()._iterencode(o, markers)

    def _iterencode_dict(self, dct, markers=None):
        for key, value in dct.items():
            if isinstance(key, str):
                yield '"' + key + '"'
            else:
                yield str(key)
            yield ':'
            for chunk in self._iterencode(value, markers):
                yield chunk


@app.post("/detect")
async def detect_anomalies(request: Request):
    global recent_data
    try:
        data_point = await request.json()
        value = data_point["value"]
        timestamp = data_point["timestamp"]

        recent_data.append(value)

        if len(recent_data) > WINDOW_SIZE:
            recent_data.pop(0)

        if len(recent_data) == WINDOW_SIZE:
            mean = statistics.mean(recent_data)
            std_dev = statistics.stdev(recent_data)
            threshold = mean + THRESHOLD_MULTIPLIER * std_dev

            if value > threshold:
                anomaly = {
                    "value": value,
                    "timestamp": timestamp,
                    "mean": mean,
                    "std_dev": std_dev
                }
                anomalies.append(anomaly)
                logger.info(f"Anomaly detected: {anomaly}")

                # Write anomaly to log file
                with open(ANOMALY_LOG_FILE, "a") as log_file:
                    log_file.write(f"{json.dumps(anomaly)}\n")

        # Write data point to log file
        with open(DATA_LOG_FILE, "a") as log_file:
            log_file.write(f"{json.dumps({'value': value, 'timestamp': timestamp})}\n")

        return JSONResponse(content={"status": "Data received and processed"})
    except Exception as e:
        logger.error(f"Failed to process data: {e}")
        raise HTTPException(status_code=500, detail="Failed to process data")


@app.get("/anomalies")
async def get_anomalies():
    return JSONResponse(content=anomalies)


@app.get("/stream_data")
async def stream_data():
    def event_stream():
        logger.info("Starting event stream for data")
        last_position = 0
        while True:
            try:
                with open(DATA_LOG_FILE, "r") as f:
                    f.seek(last_position)  # Start reading from the last position
                    lines = f.readlines()
                    last_position = f.tell()  # Update the last position

                    for line in lines:
                        data_point = json.loads(line)
                        event_data = f"data: {json.dumps(data_point)}\n\n"
                        logger.info(f"Yielding event data: {event_data}")
                        yield event_data

                if not lines:
                    time.sleep(1)  # Wait for new data if no new lines are available

            except FileNotFoundError:
                logger.warning(f"{DATA_LOG_FILE} file not found. Creating a new one.")
                open(DATA_LOG_FILE, "w").close()  # Create a new file
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error while reading {DATA_LOG_FILE}: {e}")
                time.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/stream_anomalies")
async def stream_anomalies():
    def event_stream():
        logger.info("Starting event stream for anomalies")
        last_position = 0
        while True:
            try:
                with open(ANOMALY_LOG_FILE, "r") as f:
                    f.seek(last_position)  # Start reading from the last position
                    lines = f.readlines()
                    last_position = f.tell()  # Update the last position

                    for line in lines:
                        anomaly = json.loads(line)
                        event_data = f"data: {json.dumps(anomaly)}\n\n"
                        logger.info(f"Yielding event data: {event_data}")
                        yield event_data

                if not lines:
                    time.sleep(1)  # Wait for new data if no new lines are available

            except FileNotFoundError:
                logger.warning(f"{ANOMALY_LOG_FILE} file not found. Creating a new one.")
                open(ANOMALY_LOG_FILE, "w").close()  # Create a new file
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error while reading {ANOMALY_LOG_FILE}: {e}")
                time.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/read_log")
async def read_log():
    try:
        with open(ANOMALY_LOG_FILE, "r") as log_file:
            log_content = log_file.readlines()
        return JSONResponse(content=[json.loads(line) for line in log_content])
    except Exception as e:
        logger.error(f"Failed to read log file: {e}")
        raise HTTPException(status_code=500, detail="Failed to read log file")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)