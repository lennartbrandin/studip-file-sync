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
            self.courses.append([c, f])

    def get_absolute(self, path):
        response = self.session.get(self.studip.root_url + path)
        if response.status_code != 200:
            print(f"{self.studip.root_url + path} {response.text}")
            return []
        return response.json()["data"]

    def get_api(self, route):
        return self.get_absolute(self.studip.base_route + self.studip.api_route + route)

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

    def get_files(self):
        # There is only one file ref per folder
        for file in self.get("/file-refs"):
            self.files.append(StudIPFile(self.studip, file["relationships"]["file"]["links"]["related"], self.folderpath))

    def get_folders(self):
        for folder in self.get():
            print(folder["attributes"]["name"])
            self.folders.append(StudIPFolder(self.studip, folder["relationships"]["folders"]["links"]["related"]), self.folderpath)

class StudIPFile(StudIPPath):
    def __init__(self, studip, path, filepath):
        super().__init__(studip, path)
        print(filepath + "/" + self.attributes["name"])

def main():
    url = "https://e-learning.tuhh.de/studip"
    credentials = json.load(open("credentials.json"))
    studip = StudIP(url, credentials["login"], credentials["password"])

main()