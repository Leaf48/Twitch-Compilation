import subprocess
import requests
import json
import tempfile


def get_clips(username: str, view_threshold: int, filter: str):
    url = "https://gql.twitch.tv/gql"

    payload = json.dumps(
        [
            {
                "operationName": "ClipsCards__User",
                "variables": {
                    "login": username,
                    "limit": 100,
                    "criteria": {"filter": filter, "isFeatured": False},
                    "cursor": None,
                },
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "11de2158d1eff9cbb9065f9927013e43588d675fad1e2b5efa67ed4b2156b769",
                    }
                },
            }
        ]
    )
    headers = {
        "Client-id": "kimne78kx3ncx6brgo4mv6wki5h1ko",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    data = response.json()

    _edges = data[0]["data"]["user"]["clips"]["edges"]
    _clips = [i["node"] for i in _edges if i["node"]["viewCount"] > view_threshold]

    clips = []
    for i in _clips:
        _data = {
            "slug": i["slug"],
            "url": i["url"],
            "view": i["viewCount"],
            "title": i["title"],
            "game": i["game"]["name"],
        }
        clips.append(_data)

    return clips


def download_clip(slug: str, output: str):
    cmd_json = [
        "./TwitchDownloaderCLI",
        "clipdownload",
        "--id",
        slug,
        "-o",
        output,
        "--collision",
        "Overwrite",
    ]
    subprocess.run(cmd_json)


def render_comment(slug: str, output: str):
    with tempfile.NamedTemporaryFile(delete=True, suffix=".json") as temp:
        # Download chat json
        cmd_json = [
            "./TwitchDownloaderCLI",
            "chatdownload",
            "--id",
            slug,
            "-o",
            temp.name,
            "-E",
            "--collision",
            "Overwrite",
        ]
        subprocess.run(cmd_json)

        # Render chat
        cmd_render = [
            "./TwitchDownloaderCLI",
            "chatrender",
            "-i",
            temp.name,
            "-h",
            "1080",
            "-w",
            "422",
            "--framerate",
            "30",
            "--update-rate",
            "0",
            "--font-size",
            "18",
            "--collision",
            "Overwrite",
            "-o",
            output,
        ]
        subprocess.run(cmd_render)
