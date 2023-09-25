# Music Recommendation System

This repository contains a Music Recommendation System that enables users to play/pause songs, view and play songs in their playlist, view song lyrics, and generate music recommendations based on the songs in their playlist. The system is built using PyQt6 for the GUI, Spotify API for song data, Genius Lyrics API for lyrics, and a recommendation model utilizing TF-IDF Vectorizer and Cosine Similarity.

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)

## Introduction

The Music Recommendation System is a software application that offers users the ability to manage their music, listen to songs, view lyrics, and receive recommendations based on their existing playlist. It utilizes APIs to fetch song data and lyrics and employs a recommendation model to suggest songs.

## Features

- **Play/Pause Song**: Allows users to play and pause songs.
- **View/Play Songs in Playlist**: Enables users to view and play songs present in their playlist.
- **View Song Lyrics**: Provides the lyrics for the current song being played.
- **Generate Recommendations**: Generates song recommendations based on the songs in the user's playlist.

## Technologies Used

- **PyQt6**: Python library for creating GUI applications.
- **Spotify API**: Provides song data and playback functionality.
- **Genius Lyrics API**: Fetches song lyrics.
- **Recommendation Model**:
  - **TF-IDF Vectorizer**: Converts text data into numerical representation.
  - **Cosine Similarity**: Measures similarity between songs for recommendations.

## Setup and Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/11a55an/music-recommendation-system.git
    ```

2. Install the required dependencies:

3. Set up the Spotify API and Genius Lyrics API by following their respective documentation.

4. Run the application:

    ```bash
    python main.py
    ```

## Usage

1. Open the application and authenticate with your Spotify account.

2. Play/pause songs, view your playlist, and view song lyrics.

3. Receive song recommendations based on your playlist under the Recommendations tab.
