# AMQ List Training Tool

A tool which downloads all available mp3s and stores them with new metadata indicating what song it is and where it belongs.

I've only tested this on Windows so far.

## Changes from the original version

- transcodes webms to mp3 if an mp3 is unavailable
- yaml config file
- fixed unicode/ascii issue with subprocess if invalid chars were in the command
- no more sqlite db, only checks if file already exists
- shebang for python2
- added ability to update MAL
- configurable output naming format

## Requirements

- Python 2.7
  - install required modules with `pip install selenium pyyaml` after installing python
- geckodriver.exe
  - get it [here](https://github.com/mozilla/geckodriver/releases) for your platform
  - put this in the `geckodriver` folder
- Firefox
- ffmpeg
  - install this however you want
  - if you don't add it to your PATH, put the path to your ffmpeg.exe in the config.yaml
    - e.g. `ffmpeg: "C:\ffmpeg\ffmpeg.exe"`
  - if you added it to your PATH, you can leave it as `ffmpeg: "ffmpeg"`
