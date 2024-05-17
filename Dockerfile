FROM python:3.10 


# set environment variables
#ENV PYTHONDONTWRITEBYTECODE 1
#ENV PYTHONUNBUFFERED 1
RUN pip install flask

#RUN apt-get update && apt-get install -y redis-server

COPY requirements.txt .
# install python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# running migrations
#RUN python3 sbadmin2.py

EXPOSE 5000

CMD ["python3", "sbadmin2.py"]
