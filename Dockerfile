FROM python:3.11-slim

WORKDIR /app

RUN useradd --create-home --uid 10001 bot

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=bot:bot bot.py trigger_logic.py webhook.py ./

USER bot

CMD ["python", "bot.py"]
