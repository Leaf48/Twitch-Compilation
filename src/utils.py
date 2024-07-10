import subprocess


def downloadVideo(url: str, output_title: str) -> None:
    cmd = ["streamlink", url, "best", "-f", "--output", output_title + ".mp4"]
    subprocess.run(cmd)
