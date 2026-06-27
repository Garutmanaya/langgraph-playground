FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8501

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    langgraph \
    langchain \
    langchain-openai \
    langsmith \
    python-dotenv \
    httpx

COPY agentv24_production_deployment_pattern /app/agentv24_production_deployment_pattern

EXPOSE 8501

CMD ["python", "-m", "agentv24_production_deployment_pattern.api_server"]
