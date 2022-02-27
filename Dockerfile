FROM python:3.9

WORKDIR /var/www/backend

RUN apt-get -y update && \
  apt-get install -y --no-install-recommends \
  build-essential \
  openssl libssl-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
# RUN ls ..
# COPY . /backend
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt
# CMD [ "ls" ]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
