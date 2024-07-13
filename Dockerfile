FROM python:3.12.1

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    ffmpeg \
    fontconfig \
    libfontconfig1 \
    fonts-noto-cjk

WORKDIR /app

# Install libs for python
COPY requirements.txt /app/

RUN pip install -r requirements.txt

# Download TwitchDownloaderCLI
RUN wget -O TwitchDownloaderCLI.zip https://github.com/lay295/TwitchDownloader/releases/download/1.54.9/TwitchDownloaderCLI-1.54.9-LinuxArm64.zip

RUN unzip TwitchDownloaderCLI.zip -d .

RUN rm TwitchDownloaderCLI.zip

# Add execute permissions to the CLI
RUN chmod -R +x /app/TwitchDownloaderCLI

# Set up font configuration
RUN fc-cache -fv

# App
COPY . /app/

ENTRYPOINT [ "streamlit", "run" ]

CMD [ "src/main.py" ]


