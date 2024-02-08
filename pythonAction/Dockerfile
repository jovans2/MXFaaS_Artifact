#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Dockerfile for python actions, overrides and extends ActionRunner from actionProxy
FROM whisk/dockerskeleton:vJovan

RUN apk update

ENV PACKAGES="\
    dumb-init \
    musl \
    libc6-compat \
    linux-headers \
    build-base \
    bash \
    git \
    ca-certificates \
    freetype \
    libgfortran \
    libgcc \
    libstdc++ \
    openblas \
    tcl \
    tk \
    gcc \
    make \
    curl \
    bzip2-dev \
    libssl1.1 \
    libc-dev \
    libxslt-dev \
    libxml2-dev \
    libffi-dev \
    openssl-dev \
    g++ \
    gfortran \
    vim \
    musl-dev \
    "
ENV PYTHON_PACKAGES="\
    beautifulsoup4 \
    httplib2 \
    lxml \
    python-dateutil \
    requests \
    scrapy \
    simplejson \
    virtualenv \
    twisted \
    psutil \
    joblib \
    minio \
    numpy \
    matplotlib \
    scipy \
    scikit-learn \
    pandas \
    nltk \
    opencv-python \
    "
RUN apk --update --upgrade add gcc musl-dev jpeg-dev zlib-dev libffi-dev cairo-dev pango-dev gdk-pixbuf-dev

RUN apk add --no-cache --virtual build-dependencies python3 \
    && apk add --virtual build-runtime \
    build-base python3-dev openblas-dev freetype-dev pkgconfig gfortran \
    && ln -s /usr/include/locale.h /usr/include/xlocale.h \
    && python3 -m ensurepip \
    && rm -r /usr/lib/python*/ensurepip \
    && pip3 install --upgrade pip setuptools \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && ln -sf pip3 /usr/bin/pip \
    && rm -r /root/.cache \
    && pip install --no-cache-dir $PYTHON_PACKAGES \
    && apk del build-runtime \
    && apk add --no-cache --virtual build-dependencies $PACKAGES \
    && rm -rf /var/cache/apk/*

ENV FLASK_PROXY_PORT 8080

RUN mkdir -p /pythonAction
ADD init.py /pythonAction/
ADD runner.py /pythonAction/
ADD test.txt /pythonAction
RUN rm -rf /action
RUN mkdir /action

CMD ["/bin/bash", "-c", "cd pythonAction && python3 -u init.py"]
