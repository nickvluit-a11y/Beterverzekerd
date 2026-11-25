# Beterverzekerd web app (Streamlit). Railway builds this image and sets $PORT.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
# build the DuckDB database from the committed CSVs at image build time, so the app starts fast
RUN python -m pipeline.build_db

EXPOSE 8501
CMD streamlit run app/app.py --server.port ${PORT:-8501} --server.address 0.0.0.0 --server.headless true
