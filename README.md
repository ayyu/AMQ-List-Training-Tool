# AMQ List Training Tool

A tool which downloads all available MP3 files from Expand Library for the specified list(s),
storing them with new metadata indicating what song it is and which entry it belongs to.

I've only tested this on Windows so far, but other users have reported it working on Linux.
If you're on OS X and get it working, let me know as well. Or submit a PR if it needs tweaks.

## Changes from the original version

- Moved to Python 3
  - Avoids cross-platform Unicode shenanigans
- Transcodes WebMs to MP3 if an MP3 is unavailable
- Config file changed to use YAML
  - Configurable output naming format
- No more sqlite database. The only duplicate check is if the file already exists in directory structure.
  - If you change your naming scheme, it will redownload files you already have.
- Added ability to update MAL

## Requirements

- Python 3
  - Install required modules with `pip install selenium pyyaml` after installing Python
- `geckodriver.exe`
  - Get it [here](https://github.com/mozilla/geckodriver/releases) for your platform
  - Put this in the `./vendor/` folder
- Firefox
  - If you get an error that says:

    ```sh
    Expected browser binary location, but unable to find binary in default location,
    no 'moz:firefoxOptions.binary' capability provided, and no binary flag set on the command line`,
    ```

    you can specify your Firefox install location by adding an option to the `config.yaml`: `firefox: "PATH TO FIREFOX"`
- `ffmpeg`
  - Install binaries for this however you want
  - If you didn't add `ffmpeg` to your PATH, put the path to your `ffmpeg.exe` in the `config.yaml`
    - e.g. `ffmpeg: "C:/bin/ffmpeg.exe"` if your copy of ffmpeg is stored there
    - If you want, you can place the copy of `ffmpeg.exe` in the `./vendor/` folder and set `ffmpeg: "./vendor/ffmpeg.exe"`
  - If you added it to your PATH, you can leave it as `ffmpeg: "ffmpeg"`, or just remove that line entirely
