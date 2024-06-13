# What is this
A python script to access the [Studip JSON API](https://docs.gitlab.studip.de/entwicklung/docs/jsonapi/), collect the courses of the User, recursivly collect folders & files and download them to `file_destination`

# Usage
```bash
git clone git@github.com:lennartbrandin/studip-file-sync.git
cd studip-file-sync
nano config.json # Modify the default values in the config
python studip.py
```

# Notes
To have windows compliant paths all invalid characters are replaced by "_"
https://github.com/lennartbrandin/studip-file-sync/blob/334c23cb812dc896c77cc5bfc13a8d4dd43ab36a/studip.py#L9-L12
