#!/usr/bin/env python3
 
'''
This module downloads a lot of songs from anime music quiz
Dependencies:
selenium
geckodriver
pyyaml
Firefox
ffmpeg
'''

import argparse
import json
import os
import re
import subprocess
import time
import typing

import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service

ext = 'mp3'
genre = 'Anime'
maxFilenameLength = 127
extLength = len(ext)+1

def update_list(
    driver: object,
    listType: str,
    listName: str = '') -> None:
  status = driver.find_element(By.ID, 'mpNewsContainer')
  listType = listType.upper()
  statusText = 'Updating {} with {}...'.format(listType, listName)
  driver.execute_script("document.getElementById('mpNewsContainer').innerHTML = '{}';".format(statusText))
  driver.execute_script('''new Listener('anime list update result', function (result) {
    if (result.success) {
      document.getElementById('mpNewsContainer').innerHTML = 'Update Successful: ' + result.message;
    } else {
      document.getElementById('mpNewsContainer').innerHTML = 'Update Unsuccessful: ' + result.message;
    }
  }).bindListener()''')
  driver.execute_script('''socket.sendCommand({{
    type: 'library',
    command: 'update anime list',
    data: {{
      newUsername: arguments[0],
      listType: '{}'
    }}
  }});'''.format(listType), listName)
  while True:
    if status.text != statusText:
      break
    time.sleep(0.5)


def get_question_list(driver: object) -> typing.Union[list, None]:
  driver.execute_script("document.getElementById('mpNewsContainer').innerHTML = 'Loading Expand...';")
  script ='''new Listener('expandLibrary questions', function (payload) {
    expandLibrary.tackyVariable = (JSON.stringify(payload.questions));
    document.getElementById('mpNewsContainer').innerHTML = 'Expand Loaded!'
  }).bindListener();
  socket.sendCommand({
    type: 'library',
    command: 'expandLibrary questions'
  });'''
  driver.execute_script(script)
  status = driver.find_element(By.ID, 'mpNewsContainer')
  while True:
    if status.text != 'Loading Expand...':
      break
    time.sleep(0.5)
  time.sleep(3)
  pure_string = driver.execute_script('return expandLibrary.tackyVariable')
  driver.execute_script('expandLibrary.tackyVariable = ''')
  if not pure_string:
    return
  questions = json.loads(pure_string)
  driver.execute_script("document.getElementById('mpNewsContainer').innerHTML = '';")
  return questions


def main(
    configPath: str = 'config.yaml',
    loadPath: str = '',
    dumpPath: str = '') -> None:
  config = yaml.safe_load(open(configPath))
  config['ffmpeg'] = config.get('ffmpeg', 'ffmpeg')
  config['output']['folder'] = config['output'].get('folder', './output/')
  if not loadPath:
    # log in to AMQ
    driver = webdriver.Firefox(service=Service('geckodriver/geckodriver'))
    driver.get('https://animemusicquiz.com')
    driver.find_element(By.ID, 'loginUsername').send_keys(config['user']['name'])
    driver.find_element(By.ID, 'loginPassword').send_keys(config['user']['password'])
    driver.find_element(By.ID, 'loginButton').click()
    time.sleep(10)
    # socket commands to update lists and load expand
    for listType, listName in config['list'].items():
      update_list(driver, listType=listType, listName=listName)
    questions = get_question_list(driver)
    driver.execute_script('options.logout();')
    driver.close()
  else:
    with open(loadPath, 'r') as jsonIn: questions = json.load(jsonIn)
  if dumpPath:
    with open(dumpPath, 'w') as jsonOut: json.dump(questions, jsonOut)
  # download songs from socket response
  if not questions:
    print('Expand library is empty (no list loaded or empty json loaded)')
    return
  for question in questions:
    for song in question['songs']: save(
      {'annId': question['annId'],
      'name': question['name']},
      song, config)


def save(
    anime: typing.Dict[str, str],
    song: typing.Dict[str, typing.Any],
    config: typing.Dict[str, typing.Any]) -> None:
  for key in ['mp3', '480', '720']:
    if song['versions']['open']['catbox'][key] == 1:
      format = key
      break
  if not format: return
  outputPath = build_output_path(
    anime, song,
    config['output']['folder'],
    config['output']['filename'])
  if os.path.exists(outputPath): return
  outputDir = os.path.dirname(outputPath)
  if not os.path.exists(outputDir):
    os.makedirs(outputDir)
  command = [
    '%s' % config['ffmpeg'],
    '-y',
    '-i', song['examples'][format],
    '-format',  'mp3']
  metaFlags = [
    '-map_metadata',  '-1',
    '-metadata',  'title=%s'  % song['name'],
    '-metadata',  'artist=%s' % song['artist'],
    '-metadata',  'track=%d'  % song['number'],
    '-metadata',  'disc=%d'   % song['type'],
    '-metadata',  'genre=%s'  % genre,
    '-metadata',  'album=%s'  % anime['name']]
  audioFlags = [
    '-c:a', 'copy' if format == 'mp3' else 'libmp3lame',
    '-vn',
    '-b:a', '320k',
    '-ac',  '2',
    '%s'    % outputPath]
  subprocess.call(command + metaFlags + audioFlags)
  return


def build_output_path(
    anime: typing.Dict[str, str],
    song: typing.Dict[str, typing.Any],
    outDir: str,
    nameFormat: str) -> str:
  forbidden_re = re.compile(r'<|>|:|\'|\||\?|\*|&|\^|\$|' + '\0')
  field_chars_re = re.compile(r'\.\.\.|\.\.|' + '\0')
  tokens = {
    'animeID':    anime['annId'],
    'animeName':  field_chars_re.sub('', anime['name']),
    'songID':     song['annSongId'],
    'songName':   field_chars_re.sub('', song['name']),
    'songType':   song['type'],
    'songNumber': song['number'],
    'songArtist': field_chars_re.sub('', song['artist']),
    'ext':        ext}
  path = os.path.join(
    outDir,
    forbidden_re.sub('', nameFormat.format(**tokens)))
  basename = os.path.basename(path)
  basename = basename[:maxFilenameLength-extLength] + basename[-extLength:]
  dirname = os.path.dirname(path)
  return os.path.join(basename, dirname)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--config', '-c', type=str, default='config.yaml', help='path to yaml config file')
  parser.add_argument('--load', '-l', type=str, help='path to load expand json and skip login')
  parser.add_argument('--dump', '-d', type=str, help='path to dump expand dump')
  args = parser.parse_args()
  main(args.config, args.load, args.dump)
