import subprocess


def downloadVideo(url: str, output_path: str) -> None:
    cmd = ["streamlink", url, "best", "-f", "--output", output_path]
    subprocess.run(cmd)
