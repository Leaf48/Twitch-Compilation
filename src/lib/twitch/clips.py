import os
import subprocess
import requests
import json
import tempfile
import psutil


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

    clips = []

    try:
        _edges = data[0]["data"]["user"]["clips"]["edges"]
        _clips = [i["node"] for i in _edges if i["node"]["viewCount"] > view_threshold]
    except Exception:
        return clips

    for i in _clips:
        try:
            _data = {
                "slug": i["slug"],
                "url": i["url"],
                "view": i["viewCount"],
                "title": i["title"].replace(" ", "_"),
                "game": i["game"].get("name", "undefined").replace(" ", ""),
                "createdAt": i["createdAt"],
            }
            clips.append(_data)
        except Exception:
            pass

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


def kill_process_and_children(pid):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            print(f"Killing child process: {child.pid}")
            child.kill()
        parent.kill()
        parent.wait(5)  # Wait for the parent process to exit, 5 seconds timeout
        for child in children:
            child.wait(5)  # Wait for each child process to exit
    except psutil.NoSuchProcess:
        pass


def render_comment(slug: str, output: str, timeout: int = 60) -> bool:
    with tempfile.NamedTemporaryFile(delete=True, suffix=".json") as temp:
        try:
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
            print("LOG: Downloading chat to", temp.name)
            process = subprocess.Popen(
                cmd_json, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                print("stdout:", stdout.decode())
                print("stderr:", stderr.decode())
            except subprocess.TimeoutExpired:
                print("TimeoutExpired: Killing process and children")
                kill_process_and_children(process.pid)
                stdout, stderr = process.communicate()
                print("stdout:", stdout.decode())
                print("stderr:", stderr.decode())
                return False

            if process.returncode != 0 or not os.path.exists(temp.name):
                print("Error: Chat JSON download failed.")
                return False

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
            print("LOG: Rendering chat to", output)
            process = subprocess.Popen(
                cmd_render, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                print("stdout:", stdout.decode())
                print("stderr:", stderr.decode())
            except subprocess.TimeoutExpired:
                print("TimeoutExpired: Killing process and children")
                kill_process_and_children(process.pid)
                stdout, stderr = process.communicate()
                print("stdout:", stdout.decode())
                print("stderr:", stderr.decode())
                return False

            if process.returncode != 0 or not os.path.exists(output):
                print("Error: Chat rendering failed.")
                return False

            return True
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
