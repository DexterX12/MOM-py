FROM python:3.14.0a6-bookworm

ADD . .

RUN pip install flask

EXPOSE 5000

CMD ["flask", "--app", "main", "run", "--host=0.0.0.0"]
