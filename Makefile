anomaly_server:
	cd anomaly_server
	python -m uvicorn main:app --reload

generator_server:
	cd generator_server
	python -m uvicorn main:app --port 8080 --reload