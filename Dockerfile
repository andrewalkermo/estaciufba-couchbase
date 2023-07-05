FROM couchbase/server:enterprise-7.2.0 as couchbase

COPY entrypoint.sh /config-entrypoint.sh
RUN chmod +x /config-entrypoint.sh

ENTRYPOINT ["/config-entrypoint.sh"]

FROM python:latest as estaciufba

WORKDIR /estaciufba

RUN python3 -m pip install poetry==1.5.0
RUN poetry config virtualenvs.create false

COPY pyproject.toml /estaciufba

RUN poetry install

COPY . /estaciufba

ENV PYTHONPATH="$PYTHONPATH:/estaciufba"

CMD [ "poetry", "run", "python3", "./estaciufba/main.py" ]