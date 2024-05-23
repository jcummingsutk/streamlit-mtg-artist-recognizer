#!/bin/sh
docker tag streamlit-mtg-artist-recognizer:latest registry.digitalocean.com/streamlit-apps/streamlit-mtg-artist-classifier

docker push registry.digitalocean.com/streamlit-apps/streamlit-mtg-artist-classifier:latest