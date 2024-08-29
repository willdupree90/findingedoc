FROM tensorflow/tensorflow:2.11.0-gpu

WORKDIR /temp_project

COPY ./src/ /src/

RUN cd /src/ && /usr/bin/python3 -m pip install --upgrade pip && pip install -e .

EXPOSE 8888

ENTRYPOINT ["jupyter", "lab","--ip=0.0.0.0","--allow-root","--no-browser"]