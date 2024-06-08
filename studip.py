import requests
import base64
import json
import os
from urllib.parse import urlparse

class StudIP:
    def __init__(self, url, user, password):
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

        # Get self user
        self.user = StudIPRoute(self, "/users/me")
        self.user.set_route("/users/" + self.user.id)

        # Collect user course list
        self.courses = []
        for course in self.user.get("/courses"):
            c = StudIPRoute(self, "/courses/" + course["id"])
            print(f"Course: {c.attributes['title']}")
            # Get course root folder instead of course folder
            course_root_folder = c.get("/folders")[0]["relationships"]["folders"]["links"]["related"]
            f = StudIPFolder(self, course_root_folder, "courses")
            f.download()
            self.courses.append([c, f])

    def get_absolute(self, path):
        response = self.session.get(self.studip.root_url + path)
        if response.status_code != 200:
            print(f"{self.studip.root_url + path} {response.text}")
            return {}
        return response.json()["data"]

    def get_api(self, route):
        return self.get_absolute(self.studip.base_route + self.studip.api_route + route)
    
    def warning(self, message):
        print(f"WARNING: {message}")

class StudIPPath(StudIP):
    def __init__(self, studip, path):
        self.studip = studip
        self.session = studip.session
        self.path = path
        for key, value in self.get().items():
            setattr(self, key, value)

    def set_path(self, path):
        self.path = path

    def get(self, route=""):
        return self.get_absolute(self.path + route)

class StudIPRoute(StudIPPath):
    def __init__(self, studip, route):
        super().__init__(studip, studip.base_route + studip.api_route + route)
    
    def set_route(self, route):
        self.set_path(self.studip.base_route + self.studip.api_route + route)

# Recursive folder/file structure
class StudIPFolder(StudIPPath):
    def __init__(self, studip, path, folderpath):
        # Remove trailing section
        path = "/".join(path.split("/")[:-1])
        super().__init__(studip, path)
        self.folderpath = folderpath + "/" + self.attributes["name"]
        self.files = []
        self.get_files()
        self.folders = []
        self.get_folders()

    def get_files(self):
        # There is only one file ref per folder
        for file in self.get("/file-refs"):
            if file["attributes"]["is-readable"] and file["attributes"]["is-downloadable"]:
                self.files.append(StudIPFile_ref(self.studip, file["links"]["self"], self.folderpath))
            else:
                self.warning(f"File {file['attributes']['name']} is not readable or downloadable")

    def get_folders(self):
        for folder in self.get("/folders"):
            if folder["attributes"]["is-readable"]:
                self.folders.append(StudIPFolder(self.studip, folder["relationships"]["folders"]["links"]["related"], self.folderpath))
            else:
                self.warning(f"Folder {folder['attributes']['name']} is not readable")

    def download(self):
        if not os.path.exists(self.folderpath):
            os.makedirs(self.folderpath)
        for file in self.files:
            file.download()
        for folder in self.folders:
            folder.download()

class StudIPFile_ref(StudIPPath):
    def __init__(self, studip, path, folder_path):
        super().__init__(studip, path)
        self.file_path = folder_path + "/" + self.attributes["name"]
        self.etag_path = self.file_path + ".etag"
        self.download_url = self.studip.root_url + self.path + "/content"

    def download(self):
        if os.path.exists(self.file_path) and os.path.exists(self.etag_path):
            etag = open(self.etag_path).read()
            self.download_etag(etag)
        else:
            self.download_etag("")

    def download_etag(self, etag):
        response = self.session.get(self.download_url, headers={"If-None-Match": etag})
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
    studip = StudIP(url, credentials["login"], credentials["password"])

main()