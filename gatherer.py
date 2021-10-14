#import spotify
import requests
import json
import time

AUTH_URL = "https://accounts.spotify.com/api/token"
BASE_URL = "https://api.spotify.com/v1/"

format_uri = (lambda URI : URI.split(':')[-1:][0] if (URI.find(':') != -1) else URI)
format_header = (lambda token : {"Authorization": "Bearer {}".format(token)})

def get_token(ID):
    auth_response = requests.post(AUTH_URL, {
        "grant_type": "client_credentials",
        "client_id": ID["id"],
        "client_secret": ID["secret"],
    })
    return auth_response.json()["access_token"]

def get_playlist(URI, token, bounds={"offset" : 0, "limit" : 100}):
    url = BASE_URL + "playlists/" + URI
    if bounds is not None:
        url += "/tracks?offset={}&limit={}".format(bounds["offset"], bounds["limit"])
    resp = requests.get(url, headers=format_header(token))
    return resp.json()

def get_track_features(URI, token):
    url = BASE_URL + "audio-features/" + URI
    resp = requests.get(url, headers=format_header(token))
    return resp.json()

def get_entire_playlist(URI, token):
    data = []
    bounds = {
        "offset" : 0,
        "limit" : 100
    }

    playlist = get_playlist(format_uri(URI), token)
    total = playlist["total"]

    while (bounds["offset"] + bounds["limit"] <= playlist["total"]):

        for item in playlist["items"]:
            name, uri_track = item["track"]["name"], item["track"]["uri"]
            print("{} - {}".format(name, format_uri(uri_track)))
            features = get_track_features(format_uri(uri_track), token)
            data.append(features)

        bounds["offset"] += bounds["limit"]
        playlist = get_playlist(format_uri(URI), token, bounds)
        while "error" in playlist.keys():
            print("TIMEOUT")
            time.sleep(5)
            playlist = get_playlist(format_uri(URI), token, bounds)

if __name__ == "__main__":
    credentials = None
    with open("data/credentials.json", 'r') as f:
        credentials = json.load(f)

    token = get_token(credentials)
    print("TOKEN : {}".format(token))

    data = get_entire_playlist("spotify:playlist:6u71jGN1StKMnIsnJutfsw", token)

    print("#######################################################")
    with open("data/features.json", 'w') as f:
        json.dump(data, f)
