#!/usr/bin/env python2
 
"""
This module downloads a lot of songs from anime music quiz
Dependencies:
ffmpeg
selenium
Firefox
geckodriver
"""
import os, errno, sys
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import json, yaml
import subprocess

def update_anime_lists(driver, anilist="", kitsu="", mal=""):
    print("Updating AL with {}".format(anilist))
    driver.execute_script('document.getElementById("mpNewsContainer").innerHTML = "Updating AniList...";')
    status = driver.find_element_by_id("mpNewsContainer")
    driver.execute_script("""new Listener("anime list update result", function (result) {
		if (result.success) {
			document.getElementById("mpNewsContainer").innerHTML = "Updated Successful: " + result.message;
		} else {
			document.getElementById("mpNewsContainer").innerHTML = "Update Unsuccessful: " + result.message;
		}
    }).bindListener()""")
    driver.execute_script("""
    socket.sendCommand({
		type: "library",
		command: "update anime list",
		data: {
			newUsername: arguments[0],
			listType: 'ANILIST'
		}
	});""", anilist)
    while True:
        if status.text != "Updating AniList...":
            break
        time.sleep(0.5)
    print("Updating Kitsu with {}".format(kitsu))
    driver.execute_script('document.getElementById("mpNewsContainer").innerHTML = "Updating Kitsu...";')
    driver.execute_script("""
    socket.sendCommand({
		type: "library",
		command: "update anime list",
		data: {
			newUsername: arguments[0],
			listType: 'KITSU'
		}
	});""", kitsu)
    while True:
        if status.text != "Updating Kitsu...":
            break
        time.sleep(0.5)
    print("Updating MAL with {}".format(mal))
    driver.execute_script('document.getElementById("mpNewsContainer").innerHTML = "Updating MAL...";')
    driver.execute_script("""
    socket.sendCommand({
		type: "library",
		command: "update anime list",
		data: {
			newUsername: arguments[0],
			listType: 'MAL'
		}
	});""", mal)
    while True:
        if status.text != "Updating Kitsu...":
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
    status = driver.find_element_by_id("mpNewsContainer")
    while True:
        if status.text != "Loading Expand...":
            break
        time.sleep(0.5)
    time.sleep(3)
    pure_string = driver.execute_script('return expandLibrary.tackyVariable')
    driver.execute_script('expandLibrary.tackyVariable = ""')
    if (not pure_string):
        print('Expand library is empty (no list loaded)')
        return
    ret = json.loads(pure_string)
    driver.execute_script('document.getElementById("mpNewsContainer").innerHTML = "";')
    return ret


config = []
ext = "mp3"
genre = "Anime"

def main():
    global config, ffmpeg
    config = yaml.safe_load(open("config.yaml"))
    if not config['ffmpeg']:
        config['ffmpeg'] = 'ffmpeg'
    if not config['output']['folder']:
        config['output']['folder'] = './'
    # log in to AMQ
    driver = webdriver.Firefox(executable_path='geckodriver/geckodriver')
    driver.get('https://animemusicquiz.com')
    driver.find_element_by_id("loginUsername").send_keys(config['user']['name'])
    driver.find_element_by_id("loginPassword").send_keys(config['user']['password'])
    driver.find_element_by_id("loginButton").click()
    time.sleep(10)
    # socket commands to update lists and load expand
    update_anime_lists(driver, config['list']['anilist'], config['list']['kitsu'], config['list']['mal'])
    questions = get_question_list(driver)
    driver.execute_script("options.logout();")
    driver.close()
    if (not questions):
        return
    # download songs from socket response
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
        if (song['versions']['open']['catbox'][key] == 1):
            format = key
            break
    if (not format):
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
        '"%s"' % config['ffmpeg'],
        "-y",
        '-nostats',
        "-i", song['examples'][format],
    ]
    audioFlags = [
        "-c:a", "copy",
        "-vn",
        "-b:a", "320k",
        "-ac", "2"
    ]
    if (not format == 'mp3'):
        audioFlags[1] = "libmp3lame"
    metaFlags = [
        "-map_metadata", "-1",
        "-metadata", 'title="%s"' % song['name'],
        "-metadata", 'artist="%s"' % song['artist'],
        "-metadata", 'track="%d"' % song['number'],
        "-metadata", 'disc="%d"' % song['type'],
        "-metadata", 'genre="%s"' % genre,
        "-metadata", 'album="%s"' % anime['name'],
        '"%s"' % outputPath
    ]
    # workaround to avoid utf8/ascii problems
    subprocess.call(" ".join(command + audioFlags + metaFlags).encode(sys.getfilesystemencoding()))
    return

def build_output_path(anime, song):
    forbidden_chars = re.compile(r"<|>|:|\"|\||\?|\*|&|\^|\$|" + '\0')
    tokens = {
        'animeID': anime['annId'],
        'animeName': anime['name'],
        'songID': song['annSongId'],
        'songName': song['name'],
        'songType': song['type'],
        'songNumber': song['number'],
        'songArtist': song['artist'],
        'ext': ext
    }
    tokens = {k: v.encode(sys.getfilesystemencoding()) for k, v in tokens.iteritems()}
    filename = config['output']['filename'].format(**tokens)
    filename = forbidden_chars.sub('', filename)
    path = os.path.join(config['output']['folder'], filename)
    return path

if __name__ == "__main__":
    main()
