FROM python:3

RUN mkdir -p /proxcli /src

COPY setup.py /src
COPY *.py /src/

WORKDIR /src

RUN python3 -m venv /proxcli && \
    /proxcli/bin/pip install --upgrade pip wheel setuptools && \
    /proxcli/bin/python3 setup.py install && \
    /proxcli/bin/proxcli --install-completion bash && \
    rm -Rf /stc

ENTRYPOINT [ "/proxcli/bin/proxcli" ]
CMD [ "--version" ]


