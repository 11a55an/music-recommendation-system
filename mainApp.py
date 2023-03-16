# This Python file uses the following encoding: utf-8
from PyQt6.QtWidgets import QApplication, QScrollBar, QMessageBox, QDateEdit, QMainWindow, QHBoxLayout, QVBoxLayout, QFormLayout, QWidget, QGridLayout, QStatusBar, QLabel, QPushButton, QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QToolBar
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QPixmap
from mainInterface import Ui_MainWindow
import sys
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
import lyricsgenius as lg
# import os
import re
import json
import os.path
from datetime import datetime
import time
import imageio
import pandas as pd
# from scipy import ndimage, spatial
from PIL import Image, ImageDraw
import PIL as pillow
import requests
from io import BytesIO
import numpy as np
import mysql.connector

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # Authorization
        scope = 'user-read-private user-library-read user-read-playback-state user-modify-playback-state user-top-read playlist-modify-private playlist-modify-public'
        token = util.prompt_for_user_token(scope=scope, client_id='CLIENT_ID',client_secret='CLIENT_SECRET', redirect_uri='REDIRECT_URI')
        self.sp = spotipy.Spotify(auth=token,requests_timeout=10, retries=10)
        self.sp.trace = False
        self.genius = lg.Genius(access_token="ACESS_TOKEN")
        self.currentTrack = self.sp.currently_playing()['item']['id']

        # Connect buttons
        self.homeButton.clicked.connect(lambda: self.main.setCurrentIndex(0))
        self.playingButton.clicked.connect(lambda: self.main.setCurrentIndex(1))
        self.msearchButton.clicked.connect(lambda: self.main.setCurrentIndex(2))
        self.libraryButton.clicked.connect(lambda: self.main.setCurrentIndex(3))
        self.pausePlayButton.clicked.connect(self.pausePlayPressed)
        self.nextSong.clicked.connect(self.nextPressed)
        self.prevSong.clicked.connect(self.prevPressed)
        self.volSlider.valueChanged.connect(self.volSliderMoved)
        self.searchButton.clicked.connect(self.searching)
        self.lyricsSong.clicked.connect(lambda: self.main.setCurrentIndex(4))
        
        # Connect Actions
        self.play_action.triggered.connect(lambda: self.sp.start_playback())
        self.pause_action.triggered.connect(lambda: self.sp.pause_playback())
        self.next_action.triggered.connect(lambda: self.sp.next_track())
        self.prev_action.triggered.connect(lambda: self.sp.previous_track())
        self.action100.triggered.connect(lambda: self.sp.volume(100))
        self.action80.triggered.connect(lambda: self.sp.volume(80))
        self.action60.triggered.connect(lambda: self.sp.volume(60))
        self.action40.triggered.connect(lambda: self.sp.volume(40))
        self.action20.triggered.connect(lambda: self.sp.volume(20))
        self.action0.triggered.connect(lambda: self.sp.volume(0))
        
        # Set device volume 
        devices = self.sp.devices()
        deviceVolume = [ d["volume_percent"] for d in devices["devices"]]
        if(bool(devices)):
            self.volSlider.setValue(deviceVolume[0])

        # Function Calls
        self.populateDeviceComboboxes()
        self.getProfilePic()
        self.get_time_of_day()
        self.updateCurrentTrack()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.checkForSongChange)
        self.timer.start(2000) #trigger every 2 secs
        self.timerLyrics = QtCore.QTimer()
        self.timerLyrics.timeout.connect(self.checkForLSongChange)
        self.timerLyrics.start(2000) #trigger every 2 secs
        self.getLyrics()
        
    # Set time of day for Home Screen
    def get_time_of_day(self):
        now = datetime.now().hour
        if now < 12:
            time = "morning"
        elif now < 16:
            time = "afternoon"
        elif now < 19:
            time = "evening"
        else:
            time = "night"
        timeofDay = "Good "+ time+", checkout the top songs of the day"
        self.welcomeLabel.setText(timeofDay)
    
    # Get connected devices
    def populateDeviceComboboxes(self):
        devices = self.sp.devices()
        deviceNames = [ d["name"] for d in devices["devices"] ]
        self.deviceOptions.addItems(deviceNames)

        allDevs = self.sp.devices()
        for d in allDevs["devices"]:
            if d["is_active"] == True:
                for i in range(self.deviceOptions.maxCount()):
                    if(self.deviceOptions.itemText(i) == d["name"]):
                        self.deviceOptions.setCurrentIndex(i)
                        break
                self.currentDeviceID = d["id"]
                break
        return

    # Check if the active device has changed
    def deviceComboIndexChanged(self):
        deviceReq = self.deviceOptions.currentText()
        allDevs = self.sp.devices()
        for d in allDevs["devices"]:
            if d["name"] == deviceReq:
                self.currentDeviceID = d["id"]
                break
        self.sp.transfer_playback(self.currentDeviceID)
        return

    # Check if song has changed
    def checkForSongChange(self):
        if(self.sp.currently_playing()):
            currTmp = self.sp.currently_playing()
            if(currTmp["item"]["id"] != self.currentTrackID):
                self.updateCurrentTrack()

    # Change device volume as the volume slider value changes
    def volSliderMoved(self):
        self.volume = int(self.volSlider.value())
        self.sp.volume(self.volume)
        return

    # Play Next Song
    def nextPressed(self):
        self.sp.next_track()
        self.updateCurrentTrack()
        return

    # Play previous song
    def prevPressed(self):
        self.sp.previous_track()
        self.updateCurrentTrack()
        return

    # if song has changed then update it
    def updateCurrentTrack(self):
        currentData = self.sp.currently_playing()
        if(currentData):
            self.playingNow = currentData["is_playing"]
            self.currentTrack = (currentData["item"]["name"],
                                currentData["item"]["album"]["artists"][0]["name"])
            albumArtURL = currentData["item"]["album"]["images"][0]["url"]
            self.currentTrackID = currentData["item"]["id"]
            trackName = self.currentTrack[0]
            trackName = "".join(x for x in trackName if x.isalpha())
            # Check if album cover exists then use already downloaded pic
            if os.path.isfile('images/'+trackName + '.png'):
                pixmap = QPixmap('images/'+trackName + '.png')
                self.albumArtLabel.setPixmap(pixmap.scaled(200, 200))
            else:
                try:
                    response = requests.get(albumArtURL)
                    img = Image.open(BytesIO(response.content))
                    imageio.imwrite('images/'+trackName + '.png', img)
                    pixmap = QPixmap('images/'+trackName + '.png')
                    self.albumArtLabel.setPixmap(pixmap.scaled(200, 200))
                except requests.exceptions.Timeout:
                    print ("Timeout occurred")
            self.songName.setText(self.currentTrack[0])
            self.artistName.setText(self.currentTrack[1])

    # Pause or Play the song
    def pausePlayPressed(self):
        if(self.playingNow == True):
            self.sp.pause_playback()
            self.playingNow = False
            self.pausePlayButton.setIcon(QtGui.QIcon('assets/play.svg'))
        else:
            self.sp.start_playback()
            self.playingNow = True
            self.pausePlayButton.setIcon(QtGui.QIcon('assets/pause.svg'))
        return
    
    # Get User Profile Pic 
    def getProfilePic(self):
        # Get user's profile data
        cp = self.sp.current_user()
        name = cp["display_name"]
        if os.path.isfile('images/'+name + '.png'):
                pixmap = QPixmap("images/"+name + '.png')
                self.profilePic.setPixmap(pixmap.scaled(40, 40))
        else:
            try:
                profileImageURL = cp["images"][0]["url"]
                response = requests.get(profileImageURL)
                img = Image.open(BytesIO(response.content))
                imageio.imwrite('images/'+name + '.png', img)
                pixmap = QPixmap('images/'+name + '.png')
                self.profilePic.setPixmap(pixmap.scaled(50, 50))
            except requests.exceptions.Timeout:
                print ("Timeout occurred")
        self.profileName.setText(cp["display_name"])

    # check which button is checked for Library Page  
    def checkButtonChecked(self, i):
        for x in range(self.items):
            if(self.track[x].isChecked()):
                self.sp.start_playback(uris=self.giveURI(x))
                self.track[x].toggle()

    # check which button is checked for Home Page 
    def checkHButtonChecked(self, i):
        for x in range(7):
            if(self.trackHome[x].isChecked()):
                self.sp.start_playback(uris=self.giveHURI(x))
                self.trackHome[x].toggle()

    # check which button is checked for Search Page 
    def checkSButtonChecked(self, i):
        for x in range(7):
            if(self.trackSearch[x].isChecked()):
                self.sp.start_playback(uris=self.giveSURI(x))
                self.trackSearch[x].toggle()

    # Get URI for the song to play (Library Page)
    def giveURI(self, i):
        play = self.sp.playlist_tracks("PLAYLIST_ID")
        playItem = play["items"]
        uri = playItem[i]['track']['uri']
        urilist = [uri]
        return urilist

    # Get Search results
    def searching(self):
        query = self.searchText.text()
        results = self.sp.search(query, limit=7, offset=0, type='track')
        playItem = results["tracks"]["items"]
        self.vLayout_9 = QVBoxLayout(self.widget_2)
        # print(track)
        self.trackSearch = []
        for self.i in range(len(playItem)):
            self.trackSearch.append(self.i)
            self.trackSearch[self.i] = QPushButton(parent=self.widget_2)
            self.trackSearch[self.i].setMaximumSize(QtCore.QSize(16777215, 60))
            self.trackSearch[self.i].setMinimumSize(QtCore.QSize(0, 60))
            self.trackSearch[self.i].setCheckable(True)
            self.trackSearch[self.i].setStyleSheet("color:#fff;background:#1e1e1e\n")
            self.trackSearch[self.i].setObjectName("track")
            self.vLayout_9.addWidget(self.trackSearch[self.i], QtCore.Qt.AlignmentFlag.AlignTop)
            self.horizontalLayout_29 = QHBoxLayout(self.trackSearch[self.i])
            self.horizontalLayout_29.setObjectName("horizontalLayout_22")
            self.serial = QLabel(parent=self.trackSearch[self.i])
            self.serial.setText(str(self.i+1))
            self.serial.setMaximumSize(QtCore.QSize(40, 40))
            self.serial.setMinimumSize(QtCore.QSize(40, 40))
            self.horizontalLayout_29.addWidget(self.serial)
            self.trackartLabel = QLabel(parent=self.trackSearch[self.i])
            self.trackartLabel.setObjectName("trackartLabel")
            self.trackartLabel.setMaximumSize(QtCore.QSize(60, 40))
            self.trackartLabel.setMinimumSize(QtCore.QSize(60, 40))
            trackName = playItem[self.i]['name']
            trackName = "".join(x for x in trackName if x.isalpha())
            if os.path.isfile('images/'+trackName + str(self.i)+'.png'):
                pixmap = QPixmap("images/"+trackName + str(self.i)+ '.png')
                self.trackartLabel.setPixmap(pixmap.scaled(40, 40))
            else:
                try:
                    response = requests.get(playItem[self.i]['album']['images'][0]['url'])
                    img2 = Image.open(BytesIO(response.content))
                    imageio.imwrite('images/'+ trackName + str(self.i)+ '.png', img2)
                    pixmap = QPixmap("images/"+ trackName + str(self.i)+ '.png')
                    self.trackartLabel.setPixmap(pixmap.scaled(40, 40))
                except requests.exceptions.Timeout:
                    print ("Timeout occurred")
            self.horizontalLayout_29.addWidget(self.trackartLabel)
            self.trackNameLabel =QLabel(parent=self.trackSearch[self.i])
            self.trackNameLabel.setObjectName("trackNameLabel")
            self.trackNameLabel.setText(playItem[self.i]['name'])
            self.trackNameLabel.setMaximumSize(QtCore.QSize(270, 40))
            self.trackNameLabel.setMinimumSize(QtCore.QSize(170, 40))
            self.horizontalLayout_29.addWidget(self.trackNameLabel)
            self.tartistNameLabel = QLabel(parent=self.trackHome[self.i])
            self.tartistNameLabel.setObjectName("tartistNameLabel")
            self.tartistNameLabel.setText(playItem[self.i]['artists'][0]['name'])
            self.tartistNameLabel.setMaximumSize(QtCore.QSize(270, 40))
            self.tartistNameLabel.setMinimumSize(QtCore.QSize(170, 40))
            self.horizontalLayout_29.addWidget(self.tartistNameLabel)
            self.albumName = QLabel(parent=self.trackSearch[self.i])
            self.albumName.setObjectName("albumName")
            self.albumName.setMaximumSize(QtCore.QSize(270, 40))
            self.albumName.setMinimumSize(QtCore.QSize(170, 40))
            self.albumName.setText(playItem[self.i]['album']['name'])
            self.horizontalLayout_29.addWidget(self.albumName)
            self.dateAdded = QLabel(parent=self.trackSearch[self.i])
            self.dateAdded.setObjectName("dateAdded")
            self.dateAdded.setMaximumSize(QtCore.QSize(170, 40))
            self.dateAdded.setMinimumSize(QtCore.QSize(100, 40))
            self.dateAdded.setText(playItem[self.i]['album']['release_date'])
            self.horizontalLayout_29.addWidget(self.dateAdded)
            self.trackSearch[self.i].clicked.connect(lambda a=self.i: self.checkSButtonChecked(a))

    # Get URI for the song to play (Home Page)
    def giveHURI(self, i):
        play = self.sp.playlist_tracks("PLAYLIST_ID")
        playItem = play["items"]
        uri = playItem[i]['track']['uri']
        urilist = [uri]
        return urilist

    # Get URI for the song to play (Search Page)
    def giveSURI(self, i):
        query = self.searchText.text()
        results = self.sp.search(query, limit=7, offset=0, type='track')
        playItem = results["tracks"]["items"]
        uri = playItem[i]['uri']
        urilist = [uri]
        return urilist

    def getLyrics(self):
        self.currentTrack = self.sp.currently_playing()['item']['id']
        try:
            current = self.sp.currently_playing()
        except ReadTimeout:
            current = self.sp.currently_playing()
        current_type = current['currently_playing_type']
        artist = current['item']['artists'][0]['name']
        title = current['item']['name']
        length_ms = current['item']['duration_ms']
        progress_ms = current['progress_ms']
        time_ms = length_ms - progress_ms
        time_sec = int((time_ms/1000))
        search_query = artist + " " + title

        song = self.genius.search_song(title=title, artist=artist)
        try:
            lyrics = song.lyrics
            url = song.url
            self.lyricsMain.setText(str(lyrics))
        except:
            self.lyricsMain.setText("Sorry! Lyrics not available for this song.")

    def checkForLSongChange(self):
        if(self.sp.currently_playing()):
            currTmp = self.sp.currently_playing()
            if(currTmp["item"]["id"] != self.currentTrack):
                self.getLyrics()

# Main Driver Code
if __name__ == "__main__":
    app = QApplication(sys.argv)
    splashPic = QtGui.QPixmap('assets/spotify.png')
    splash = QtWidgets.QSplashScreen(splashPic.scaled(200,200))
    step = 0.1
    opaqueness = 0.0
    splash.setWindowOpacity(opaqueness)
    # splash.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    splash.show()
    while opaqueness < 1:
        splash.setWindowOpacity(opaqueness)
        time.sleep(step)
        opaqueness+=step
    time.sleep(1)
    splash.close()
    win = MainWindow()
    win.setWindowTitle("Spotify Music Recommendation App")
    win.setWindowIcon(QtGui.QIcon('assets/spotify.png'))
    win.show()
    sys.exit(app.exec())
