FROM python:3.11.10
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
COPY . /code

RUN pip install --upgrade pip
RUN pip install spacy
RUN apt-get update && apt-get -y install ghostscript
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
RUN pip install deep_translator
RUN pip install -r ./requirements.txt

COPY ./entrypoint.sh /
ENTRYPOINT ["sh", "/entrypoint.sh"]



