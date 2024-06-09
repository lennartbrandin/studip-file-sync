import requests
import base64
import json
import os
import sqlite3
from urllib.parse import urlparse

class db:
    def __init__(self, path):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.cursor = self.conn.cursor()

    def execute(self, query):
        self.cursor.execute(query)
        self.conn.commit()

    def close(self):
        self.conn.close()

class StudIP:
    def __init__(self, db, url, user, password):
        self.db = db
        parse = urlparse(url)
        self.root_url = f"{parse.scheme}://{parse.netloc}"
        self.base_route = parse.path
        self.api_route = "/jsonapi.php/v1"
        self.username = user
        self.password = password
        self.session = requests.Session()
        self.headers = {
                "Authorization": "Basic " + base64.b64encode(f"{self.username}:{self.password}".encode()).decode(),
        }
        self.session.headers.update(self.headers)
        self.studip = self # Inherited attribute
        self.setup()

    def setup(self):
        self.user = StudIPRoute(self, self.get_raw_api("/users/me").json()["data"])

        # Collect user course list
        self.courses = []
        for course in self.user.get_sub("/courses"):
            c = StudIPRoute(self, course)
            print(f"Course: {c.attributes['title']}")
            # Get course root folder instead of course folder
            f = StudIPFolder(self, c.get_sub("/folders")[0], "./courses")
            f.download()
            self.courses.append([c, f])

    def get_raw_absolute(self, path, additional_headers):
        """Get json data from root_url + path"""
        headers = self.session.headers.copy()
        headers.update(additional_headers)
        response = self.session.get(self.studip.root_url + path, headers=headers)
        if response.status_code != 200:
            print(f"{self.studip.root_url + path} {response.text}")
        return response
    
    def get_raw_api(self, route, headers=""):
        """Get root_url + api_route + route"""
        return self.get_raw_absolute(self.studip.base_route + self.studip.api_route + route, headers)
    
    def warning(self, message):
        print(f"WARNING: {message}")

class StudIPRoute(StudIP):
    """Object that behaves relative to route"""
    def __init__(self, studip, data):
        self.studip = studip
        self.session = studip.session
        for key, value in data.items():
            setattr(self, key, value)

    def get_raw_sub(self, route="", headers=""):
        return self.get_raw_api("/"+ self.type +"/"+ self.id + route, headers)

    def get_sub(self, route="", headers=""):
        return self.get_raw_sub(route, headers).json()["data"]
    
class StudIPFolder(StudIPRoute):
    def __init__(self, studip, data, folder_path):
        super().__init__(studip, data)
        self.folder_path = folder_path + "/" + self.attributes["name"]
        self.files_refs = []
        self.folders = []
        self.get_file_refs()
        self.get_folders()

    def get_file_refs(self):
        for file_ref in self.get_sub("/file-refs"):
            if file_ref["attributes"]["is-readable"] and file_ref["attributes"]["is-downloadable"]:
                self.files_refs.append(StudIPFile_ref(self.studip, file_ref, self.folder_path))
            else:
                self.warning(f"File {file_ref['attributes']['name']} is not readable or downloadable")

    def get_folders(self):
        for folder in self.get_sub("/folders"):
            if folder["attributes"]["is-readable"]:
                self.folders.append(StudIPFolder(self.studip, folder, self.folder_path))            
            else:
                self.warning(f"Folder {folder['attributes']['name']} is not readable")

    def download(self):
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folderpath)
        for file_ref in self.files_refs:
            file_ref.download()
        for folder in self.folders:
            folder.download()

class StudIPFile_ref(StudIPRoute):
    def __init__(self, studip, data, folder_path):
        super().__init__(studip, data)
        self.file_path = folder_path + "/" + self.attributes["name"]
        self.etag_path = self.file_path + ".etag"

    def download(self):
        if os.path.exists(self.file_path) and os.path.exists(self.etag_path):
            etag = open(self.etag_path).read()
            self.download_etag(etag)
        else:
            self.download_etag("")

    def download_etag(self, etag):
        response = self.get_raw_sub("/content", headers={"If-None-Match": etag})
        if response.status_code == 200:
            with open(self.file_path, "wb") as f:
                f.write(response.content)
            with open(self.etag_path, "w") as f:
                f.write(response.headers["ETag"])
        elif response.status_code == 304:
            self.studip.warning(f"File {self.file_path} is up to date")
        else:
            self.studip.warning(f"Failed to download {self.file_path} {response.text}")

def main():
    url = "https://e-learning.tuhh.de/studip"
    credentials = json.load(open("credentials.json"))
    studip_db = db("studip.db")
    studip = StudIP(studip_db, url, credentials["login"], credentials["password"])
main()