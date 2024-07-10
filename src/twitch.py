import json
import requests


class Twitch:
    def __init__(self, streamer: str) -> None:
        self.streamer = streamer

    def getClips(self, filter: str):
        endpoint = "https://gql.twitch.tv/gql"

        body = json.dumps(
            [
                {
                    "operationName": "ClipsCards__User",
                    "variables": {
                        "login": self.streamer,
                        "limit": 20,
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

        res = requests.post(endpoint, data=body, headers=headers)

        clips = []
        if res.status_code == 200:
            res = res.json()
            for i in res[0]["data"]["user"]["clips"]["edges"]:
                clip = {
                    "url": i["node"]["url"],
                    "title": i["node"]["title"],
                    "view": i["node"]["viewCount"],
                    "duration": i["node"]["durationSeconds"],
                    "genre": i["node"]["game"]["name"],
                    "slug": i["node"]["slug"],
                }
                clips.append(clip)
            clips.sort(key=lambda x: x["view"], reverse=True)

        return clips
