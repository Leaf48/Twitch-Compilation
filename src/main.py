import subprocess
from twitch import Twitch


def downloadVideo(url: str, output: str) -> None:
    cmd = ["streamlink", url, "best", "--output", output]
    subprocess.run(cmd)


t = Twitch("")
clips = t.getClips("LAST_DAY")
for i in clips:
    downloadVideo(i["url"], i["slug"])
