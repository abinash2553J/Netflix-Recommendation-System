FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
COPY data ./data
RUN pip install --no-cache-dir ".[serve]"
ENV NETFLIX_DATA=/app/data/netflixData.csv
EXPOSE 8000
CMD ["uvicorn", "netflix_recsys.api:app", "--host", "0.0.0.0", "--port", "8000"]
