FROM python:3.7

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py /
RUN chmod +x /main.py

ENTRYPOINT [ "/main.py" ]
# [ "python", "./main.py" ]