import requests
import json
import time
import os

AUTH_URL = "https://accounts.spotify.com/api/token"
BASE_URL = "https://api.spotify.com/v1/"

format_uri = (lambda URI : URI.split(':')[-1:][0] if (URI.find(':') != -1) else URI)
format_header = (lambda token : {"Authorization": "Bearer {}".format(token)})

class CollectMusic(object):
    def __init__(self, credentials_file):
        self.credentials = {}
        with open(credentials_file, 'r') as f:
            self.credentials = json.load(f)
        self.token = None
        self.response = None

        self.bounds = { "offset" : 0, "limit" : 0 }

    def get_token(self):
        auth_response = requests.post(AUTH_URL, {
            "grant_type": "client_credentials", #set it to 'refresh_token'  
            "client_id": self.credentials["id"],
            "client_secret": self.credentials["secret"],
        })
        self.token = auth_response.json()["access_token"]
        return self

    def request(self, url):
        try:
            resp = requests.get(url, headers=format_header(self.token))
            self.response = resp.json()

            if "error" in self.response.keys():
                print("HANDLE : ", self.response)
                self.handle_error(url)

        except Exception as e:
            print("ERROR(request): ", str(e))
            print("Received: ", resp.content)
            self.response = {}

        return self.response

    def handle_error(self, url):
        status = self.response["error"]["status"]
        if status == 429:
            print("###TIMEOUT###")
            time.sleep(5)
            return self.request(url)
        elif status == 401:
            print("###UNAUTHORIZED###")
            self.get_token()
            return self.request(url)
        elif status == 404:
            print("URL : ", url)
            self.response = {}
            return self
        else:
            print("URL : ", url)
            print(self.response)
            print("###Unhandled Error###")
            self.response = {}
            return self

    def get_all(self, url, gatherer=None, key=None, bounds=None):
        data = []
        self.bounds = bounds if bounds is not None else {"offset":0, "limit":10}

        self.request(url)
        if self.response == {}:
            return data
        if len(list(self.response.keys())) == 1:
            self.response = self.response[list(self.response.keys())[0]]

        while (self.bounds["offset"] == 0 or len(data) < self.response["total"]):

            try:
                # item = None
                # for item in self.response["items"]:
                #     # if item is not None:
                #     if key is not None:
                #         item = item[key]
                #     elif gatherer is not None:
                #         item = gatherer(item)
                #     data.append(item)
                # print("GET_ALL({}/{})".format(len(data), self.response["total"]))
                # if self.response["items"] is not None:
                if key is not None:
                    data += [item[key] for item in self.response["items"]]
                elif gatherer is not None:
                    data += [gatherer(item) for item in self.response["items"]]
                else:
                    data += [item for item in self.response["items"]]
                self.bounds["offset"] += len(self.response["items"])
            except Exception as e:
                print("ERROR(get_all): ", str(e))
                print(self.response)


            self.request(url + "?offset={}&limit={}".format(self.bounds["offset"], self.bounds["limit"]))
            if self.response == {}:
                return data
            if len(list(self.response.keys())) == 1:
                self.response = self.response[list(self.response.keys())[0]]

        return data

    def get_categories(self):
        url = BASE_URL + "browse/categories"
        return self.get_all(url, key="id", bounds={"offset":0, "limit":50})

    def get_category_playlists(self, category):
        url = BASE_URL + "browse/categories/{}/playlists".format(category)
        return self.get_all(url, key="uri", bounds={"offset":0, "limit":50})

    def get_playlist_tracks(self, playlist):
        url = BASE_URL + "playlists/{}/tracks".format(format_uri(playlist))
        f = (lambda x : x["track"]["uri"] if x["track"] is not None else None)
        return self.get_all(url, gatherer=f, bounds={"offset":0, "limit":100})

    def get_audio_features(self, tracks):
        if len(tracks) > 30:
            feats = []
            split = 20
            for i in range(0, len(tracks), split):
                ids = ",".join([format_uri(uri) for uri in tracks[slice(i, i+split, 1)]])
                url = BASE_URL + "audio-features?ids={}".format(ids)
                feats += self.request(url)["audio_features"]
            return {"audio_features" : feats}
        else:
            ids = ",".join([format_uri(uri) for uri in tracks])
            url = BASE_URL + "audio-features?ids={}".format(ids)
            return self.request(url)

if __name__ == "__main__":
    collector = CollectMusic("credentials.json")
    collector.get_token()
    print(collector.token)


    for cat in collector.get_categories():
        print("CATEGORY : ", cat)

        data = []
        for playlist in collector.get_category_playlists(cat):

            print("\tGET_PLAYLIST : ", playlist)
            tracks = collector.get_playlist_tracks(playlist)
            tracks = [x for x in tracks if x is not None]
            features = collector.get_audio_features(tracks)
            data += features["audio_features"]

        with open("data/{}.json".format(cat), 'a') as f:
            json.dump(data, f)

