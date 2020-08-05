FROM python:3.7-slim

COPY requirements.txt .
RUN pip install -r requrements.txt

ENTRYPOINT [ "python", "main.py" ]