import os
import requests


def get_room_id() -> str:
    try:
        url = "https://api.videosdk.live/v2/rooms"
        header = {'Authorization': os.getenv('VIDEO_SDK_API_KEY'), }
        response = requests.post(url, headers=header)
        print(response.status_code)
        print(response.json())
        return response.json()["roomId"]
    except Exception as e:
        raise e
