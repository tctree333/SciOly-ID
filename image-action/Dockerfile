FROM python:3.7-slim

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .
COPY generate_hashes_ids.py .

ENTRYPOINT [ "/usr/bin/python", "main.py" ]