#!/usr/bin/env python3
 
"""
This module downloads a lot of songs from anime music quiz
Dependencies:
ffmpeg
selenium
Firefox
geckodriver
"""
import os, errno
import re
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
import time
import json, yaml
import subprocess
import argparse

config = {}
ext = "mp3"
genre = "Anime"


def update_list(driver, listType, listName=""):
    status = driver.find_element(By.ID, "mpNewsContainer")
    listType = listType.upper()
    statusText = "Updating {} with {}...".format(listType, listName)
    driver.execute_script('document.getElementById("mpNewsContainer").innerHTML = "{}";'.format(statusText))
    driver.execute_script("""new Listener("anime list update result", function (result) {
        if (result.success) {
            document.getElementById("mpNewsContainer").innerHTML = "Update Successful: " + result.message;
        } else {
            document.getElementById("mpNewsContainer").innerHTML = "Update Unsuccessful: " + result.message;
        }
    }).bindListener()""")
    driver.execute_script("""socket.sendCommand({{
        type: "library",
        command: "update anime list",
        data: {{
            newUsername: arguments[0],
            listType: '{}'
        }}
    }});""".format(listType), listName)
    while True:
        if status.text != statusText:
            break
        time.sleep(0.5)


def get_question_list(driver):
    driver.execute_script('document.getElementById("mpNewsContainer").innerHTML = "Loading Expand...";')
    script ="""new Listener("expandLibrary questions", function (payload) {
        expandLibrary.tackyVariable = (JSON.stringify(payload.questions));
        document.getElementById("mpNewsContainer").innerHTML = "Expand Loaded!"
    }).bindListener();
    socket.sendCommand({
        type: "library",
        command: "expandLibrary questions"
    });"""
    driver.execute_script(script)
    status = driver.find_element(By.ID, "mpNewsContainer")
    while True:
        if status.text != "Loading Expand...":
            break
        time.sleep(0.5)
    time.sleep(3)
    pure_string = driver.execute_script('return expandLibrary.tackyVariable')
    driver.execute_script('expandLibrary.tackyVariable = ""')
    if not pure_string:
        return
    ret = json.loads(pure_string)
    driver.execute_script('document.getElementById("mpNewsContainer").innerHTML = "";')
    return ret


def main(configPath="config.yaml", loadPath="", dumpPath=""):
    global config
    config = yaml.safe_load(open(configPath))
    config['ffmpeg'] = config.get('ffmpeg', 'ffmpeg')
    config['output']['folder'] = config['output'].get('folder', './output/')
    if not loadPath:
        # log in to AMQ
        driver = webdriver.Firefox(service=Service('geckodriver/geckodriver'))
        driver.get('https://animemusicquiz.com')
        driver.find_element(By.ID, "loginUsername").send_keys(config['user']['name'])
        driver.find_element(By.ID, "loginPassword").send_keys(config['user']['password'])
        driver.find_element(By.ID, "loginButton").click()
        time.sleep(10)
        # socket commands to update lists and load expand
        for listType, listName in config['list'].items():
            update_list(driver, listType=listType, listName=listName)
        questions = get_question_list(driver)
        driver.execute_script("options.logout();")
        driver.close()
    else:
        with open(loadPath, 'r') as jsonIn:
            questions = json.load(jsonIn)
    if dumpPath:
        with open(dumpPath, 'w') as jsonOut:
            json.dump(questions, jsonOut)
    # download songs from socket response
    if not questions:
        print('Expand library is empty (no list loaded or empty json loaded)')
        return
    for question in questions:
        anime = {
            "annId": question["annId"],
            "name": question["name"]
        }
        songs = question["songs"]
        for song in songs:
            save(anime, song)


def save(anime, song):
    format = ""
    for key in ['mp3', '480', '720']:
        if song['versions']['open']['catbox'][key] == 1:
            format = key
            break
    if not format:
        return
    outputPath = build_output_path(anime, song)
    if os.path.exists(outputPath):
        return
    if not os.path.exists(os.path.dirname(outputPath)):
        try:
            os.makedirs(os.path.dirname(outputPath))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
    command = [
        config['ffmpeg'],
        '-y',
        '-i', song['examples'][format],
    ]
    audioFlags = [
        '-c:a', 'copy',
        '-vn',
        '-b:a', '320k',
        '-ac', '2'
    ]
    if not format == 'mp3':
        audioFlags[1] = 'libmp3lame'
    metaFlags = [
        "-map_metadata", "-1",
        "-metadata", 'title=%s' % song['name'],
        "-metadata", 'artist=%s' % song['artist'],
        "-metadata", 'track=%d' % song['number'],
        "-metadata", 'disc=%d' % song['type'],
        "-metadata", 'genre=%s' % genre,
        "-metadata", 'album=%s' % anime['name'],
        '%s' % outputPath
    ]
    proc = command + audioFlags + metaFlags
    subprocess.call(proc)
    return


def build_output_path(anime, song):
    forbidden_chars = re.compile(r"<|>|:|\"|\||\?|\*|&|\^|\$|" + '\0')
    relative_chars = re.compile(r"\.\.\.|\.\.|" + '\0')
    tokens = {
        'animeID': anime['annId'],
        'animeName': relative_chars.sub('', anime['name']),
        'songID': song['annSongId'],
        'songName': relative_chars.sub('', song['name']),
        'songType': song['type'],
        'songNumber': song['number'],
        'songArtist': relative_chars.sub('', song['artist']),
        'ext': ext
    }

    filename = config['output']['filename'].format(**tokens)
    filename = forbidden_chars.sub('', filename)
    path = os.path.join(config['output']['folder'], filename)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', type=str, default='config.yaml', help='path to yaml config file')
    parser.add_argument('--load', '-l', type=str, help='path to load expand json and skip login')
    parser.add_argument('--dump', '-d', type=str, help='path to dump expand dump')
    args = parser.parse_args()
    main(args.config, args.load, args.dump)
