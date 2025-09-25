FROM python:3.10-alpine

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache -i https://pypi.mirrors.ustc.edu.cn/simple/ poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY app.py ./app.py
COPY api ./api
COPY crypt ./crypt
COPY middleware ./middleware
COPY modules ./modules
COPY server ./server
COPY utils ./utils
COPY static ./static
COPY res ./res

CMD [ "python", "app.py" ]
