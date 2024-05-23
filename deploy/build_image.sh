#!/bin/sh
echo "downloading the model"
python -m model_downloader.main --config-file model_downloader/config.yaml --config-secrets-file model_downloader/config_secret.yaml

echo "downloading image files"
python -m image_downloader.main --image-config-file image_downloader/config.yaml --num-images-per-artist=12

docker build -t streamlit-mtg-artist-recognizer ./st_app

rm -r st_app/model/
rm -r st_app/images/