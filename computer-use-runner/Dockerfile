FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        xvfb \
        x11-utils \
        tesseract-ocr \
        scrot \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Live Agent-S: build with --build-arg INSTALL_GUI_AGENTS=1
ARG INSTALL_GUI_AGENTS=0
RUN if [ "$INSTALL_GUI_AGENTS" = "1" ]; then pip install --no-cache-dir gui-agents pyautogui; fi

COPY app ./app

RUN mkdir -p /var/titan/cu-artifacts

ENV AGENT_S_MODE=stub
ENV COMPUTER_USE_ARTIFACT_DIR=/var/titan/cu-artifacts
ENV DISPLAY=:99

EXPOSE 8090

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090"]
