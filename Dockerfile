FROM python:3.10-alpine

WORKDIR /app

# 第一阶段：只复制依赖文件（最大化缓存命中率）
COPY pyproject.toml ./

# 安装依赖（此层会被缓存，除非 pyproject.toml 变化）
RUN pip install --no-cache-dir -i https://pypi.mirrors.ustc.edu.cn/simple/ .

# 第二阶段：复制应用代码（代码变化不会导致依赖重装）
COPY main.py ./main.py
COPY routers ./routers
COPY middleware ./middleware
COPY modules ./modules
COPY server ./server
COPY utils ./utils
COPY static ./static

CMD [ "python", "main.py" ]
