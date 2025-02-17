FROM python:3.12

RUN pip install 'zarr==3.0.2'

COPY get_metric.py /

ENTRYPOINT [ "python", "/get_metric.py" ]
