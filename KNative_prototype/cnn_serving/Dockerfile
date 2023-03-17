FROM jovanvr97/cnn_serve_start

RUN pip install sockets pickle-mixin requests psutil js2py JPype1 redis Flask numpy jsonpickle
RUN mkdir -p /pythonAction
ADD runner.py /pythonAction/
ADD app.py /pythonAction/
ADD dnld_blob.py /pythonAction/

CMD cd pythonAction && python3 -u runner.py