# What is this
A python script to access the [Studip JSON API](https://docs.gitlab.studip.de/entwicklung/docs/jsonapi/), collect the courses of the User, recursivly collect folders & files and download them to `file_destination`

# Usage
```bash
git clone git@github.com:lennartbrandin/studip-file-sync.git
cd studip-file-sync
nano config.json # Modify the default values in the config
python studip.py
```
Example of resulting structure in the `file_destination`
```
SoSe 24
├── Seminar
│   └── Grundlagen der Gruppenleitung und Didaktik am Beispiel von Robotik- und Technikkursen_Tutorenausbildung robotik@TUHH (SE) [BA]
├── sonstige
│   └── Language Café@TUHH - English
├── Übung
│   └── Elektrotechnik II_ Wechselstromnetzwerke und grundlegende Bauelemente (GÜ)
└── Vorlesung
    ├── Elektrotechnik II_ Wechselstromnetzwerke und grundlegende Bauelemente (VL)
    └── Objektorientierte Programmierung, Programmierparadigmen
WiSe 23_24
├── Übung
│   └── Diskrete Algebraische Strukturen (GÜ)
└── Vorlesung
    ├── Diskrete Algebraische Strukturen (VL)
    └── [Vorlesung & Übung] Elektrotechnik I_ Gleichstromnetzwerke und elektromagnetische Felder
```

# Notes
To have windows compliant paths all invalid characters are replaced by "_"
https://github.com/lennartbrandin/studip-file-sync/blob/334c23cb812dc896c77cc5bfc13a8d4dd43ab36a/studip.py#L9-L12
