import argparse
import json
import os
import shutil
import time
from argparse import Namespace

import requests
import yaml
from mtgsdk import Card
from requests import Response


def get_unique_cards(cards: list[Card]) -> list[Card]:
    included_card_names: list[str] = []
    unique_cards: list[Card] = []
    for card in cards:
        if card.name not in included_card_names:
            unique_cards.append(card)
            included_card_names.append(card.name)
    return unique_cards


def get_card_names_for_artist(artist: str, num_cards: int) -> list[Card]:
    cards = Card.where(artist=artist).all()
    cards_to_return = get_unique_cards(cards)[:num_cards]
    return cards_to_return


def format_artist_name_for_folder(name: str) -> str:
    """converts a name such as John Avon to john_avon"""
    name = name.lower()
    name_split = str.split(name)

    folder_name = "_".join(name_split)
    return folder_name


def get_image_uri(input_multiverse_id: str):
    """Get the uris of image (without card border) in the input_multiverse_id from the
    scryfall api

    Args:
        input_multiverse_id (str): id for mtg card to get url for

    Returns:
        str: uri for the image
    """

    api_link = f"https://api.scryfall.com/cards/multiverse/{input_multiverse_id}"

    response = requests.get(api_link)
    if response.status_code == 200:
        response_json = response.json()
        try:
            image_uri = response_json["image_uris"]["art_crop"]
        except KeyError:
            image_uri = None
        time.sleep(0.1)  # API requests to wait 50-100 ms per request
        return image_uri
    return None


def copy_response_to_file(response: Response, filename: str):
    """Copies the response of an api call, which should be an image, to the filename

    Args:
        response (Response): Response with image
        filename (str): filename to save
    """
    if response.status_code == 200:
        response.raw.decode_content = True
        with open(filename, "wb") as f:
            shutil.copyfileobj(response.raw, f)


def download_card_images(cards: list[Card], folder_dir: str):
    """Download all images of the list of cards to the folder dir

    Args:
        cards (list[Card]): list of cards' images to download
        folder_dir (str): relative folder directory to save them in
    """

    for card in cards:
        filename = os.path.join(folder_dir, f"{card.multiverse_id}.jpg")

        image_uri = get_image_uri(card.multiverse_id)

        if image_uri is not None:
            response = requests.get(image_uri, stream=True)
            time.sleep(0.1)  # API requests to wait 50-100 ms per request
            copy_response_to_file(response=response, filename=filename)


def download_images_for_artist(artist: str, num_images: int, image_folder: str):
    artist_dir = os.path.join(
        f"{image_folder}", f"{format_artist_name_for_folder(artist)}"
    )
    os.makedirs(artist_dir, exist_ok=True)
    cards = get_card_names_for_artist(artist, num_images)
    download_card_images(cards, artist_dir)


def parse_arguments() -> Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--image-config-file",
        type=str,
        default=os.path.join("image_downloader", "config.yaml"),
    )
    parser.add_argument("--num-images-per-artist", type=int, default=10)
    args = parser.parse_args()
    return args


def get_image_config(
    image_config_file: str = os.path.join("image_downloader", "config.yaml")
):
    with open(image_config_file, "r") as f:
        image_config = yaml.safe_load(f)
    return image_config


def main(artists: list[str], num_images_per_artist: int, image_folder: str):
    for artist in artists:
        download_images_for_artist(artist, num_images_per_artist, image_folder)


def get_artists() -> list[str]:
    artist_mapping_file = os.path.join(
        "model", "mtg-artist-classifier", "model", "code", "artist_mapping.json"
    )
    with open(artist_mapping_file, "r") as f:
        artist_mapping_dict = json.load(f)
    artists = [artist for artist in artist_mapping_dict.values()]
    return artists


if __name__ == "__main__":
    args = parse_arguments()
    image_config_file = args.image_config_file
    num_images_per_artist = args.num_images_per_artist

    image_config = get_image_config()
    artists = get_artists()
    image_folder = image_config["images_dir"]

    main(artists, num_images_per_artist, image_folder)
