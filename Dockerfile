FROM python:3.10-alpine

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache -i https://pypi.mirrors.ustc.edu.cn/simple/ .

COPY main.py ./main.py
COPY api ./api
COPY crypt ./crypt
COPY middleware ./middleware
COPY modules ./modules
COPY server ./server
COPY utils ./utils
COPY static ./static
COPY res ./res

CMD [ "python", "main.py" ]
