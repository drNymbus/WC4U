#import spotify
import requests
import json
import time
import os

AUTH_URL = "https://accounts.spotify.com/api/token"
BASE_URL = "https://api.spotify.com/v1/"

format_uri = (lambda URI : URI.split(':')[-1:][0] if (URI.find(':') != -1) else URI)
format_header = (lambda token : {"Authorization": "Bearer {}".format(token)})

def remove_duplicates_tracks(tracks): # https://stackoverflow.com/questions/9427163/remove-duplicate-dict-in-list-in-python
    '''
    ça fonctionne ap, au pire on peut le faire dans le notebook
    mais le mieux ça serait de le faire avant de l'enregistrer
    (quoi que une musique peut s'inscrire dans differents styles)
    '''
    if tracks != []:
        to_del = []
        for i in range(len(tracks)-1, 0, -1):
            for j in range(i-1, 0, -1):
                # print(len(tracks), i, j)
                if tracks[i]["uri"] == tracks[j]["uri"]:
                    to_del.append(j)

        for index in to_del[::-1]:
            del tracks[index]

    return tracks
    # return [i for n, i in enumerate(tracks) if i not in tracks[n + 1:]]

def get_token(ID):
    auth_response = requests.post(AUTH_URL, {
        "grant_type": "client_credentials",
        "client_id": ID["id"],
        "client_secret": ID["secret"],
    })
    return auth_response.json()["access_token"]

def get_categories(token):
    url = BASE_URL + "browse/categories"
    resp = requests.get(url, headers=format_header(token))
    data = resp.json()["categories"]
    return [item["id"] for item in data["items"]][1:]

def get_category_playlists(category, token):
    url = BASE_URL + "browse/categories/{}/playlists".format(category)
    resp = requests.get(url, headers=format_header(token))
    return resp.json()

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
            try:
                name, uri_track = item["track"]["name"], item["track"]["uri"]
                print("\t\t{} - {}".format(name, format_uri(uri_track)))
                features = get_track_features(format_uri(uri_track), token)
                data.append(features)
            except:
                print("Error loading item : {}".format(item))

        bounds["offset"] += bounds["limit"]
        playlist = get_playlist(format_uri(URI), token, bounds)
        while "error" in playlist.keys():
            print("TIMEOUT")
            time.sleep(5)
            playlist = get_playlist(format_uri(URI), token, bounds)

    return data

def save_category(category, i, tracks):
    try:
        filename = "data/{}_{}.json".format(category, i)
        with open(filename, 'a') as f:
            json.dump(tracks, f)
    except Exception as e:
        print("Error saving JSON : ", str(e))

if __name__ == "__main__":
    credentials = None
    with open("data/credentials.json", 'r') as f:
        credentials = json.load(f)

    token = get_token(credentials)
    print("TOKEN : {}".format(token))

    for i, category in enumerate(get_categories(token)):
        print("({})CATEGORY : {}".format(i, category))

        playlists = get_category_playlists(category, token)
        data = []

        if "playlists" in playlists.keys():
            for playlist in playlists["playlists"]["items"]:

                print("\tPLAYLIST : {}\n\tdesc: {}".format(playlist["name"], playlist["description"]))

                data += get_entire_playlist(playlist["uri"], token)
                # data = remove_duplicates_tracks(data)
        save_category(category, i, data)

    print("DONE")
