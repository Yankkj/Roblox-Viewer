FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r <(python - <<'PY'\nimport tomllib,sys;print('\\n'.join(['aiohttp>=3.9.0']))\nPY) || pip install aiohttp>=3.9.0
CMD ["python","main.py"]
