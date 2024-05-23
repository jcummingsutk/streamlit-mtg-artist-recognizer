import json
import os

import mlflow
import streamlit as st
import torch
from model.code.prepare_data_constants import IMAGE_TRANSFORMS
from PIL import Image
from streamlit_image_select import image_select


def page_config():
    st.set_page_config(
        layout="centered",
    )
    st.markdown(
        "<style>div.block-container{padding-top:1rem;}</style>", unsafe_allow_html=True
    )
    st.markdown(
        "<h1 style='text-align: center; color: white;'>Magic: The Gathering Artist Recognizer</h1>",
        unsafe_allow_html=True,
    )


def folder_name_to_artist(folder_name: str) -> str:
    """converts john_avon -> John Avon"""
    name_as_list = str.split(folder_name, "_")
    name_as_list = [name[0].upper() + name[1:] for name in name_as_list]
    name = " ".join(name_as_list)
    return name


def load_image_selection() -> str:
    root_image_dir = "st_app/images"
    artists_dirs = os.listdir(root_image_dir)

    artists = [folder_name_to_artist(artist) for artist in artists_dirs]

    artists_dirs_dict: dict[str, str] = {
        artist_name: os.path.join(root_image_dir, artist_folder)
        for artist_name, artist_folder in zip(artists, artists_dirs)
    }

    artist = st.selectbox("Select an artist", artists)
    artist_image_dir = artists_dirs_dict[artist]

    image_filenames = os.listdir(artist_image_dir)
    img = image_select(
        label="Select an image",
        images=[
            os.path.join(f"{artist_image_dir}/", f"{num}") for num in image_filenames
        ],
        use_container_width=False,
    )
    return img


def get_model():
    device = torch.device("cpu")
    model = mlflow.pytorch.load_model("./st_app/model/", map_location=device)
    return model


def get_artist_dict() -> dict[str, str]:
    with open(
        os.path.join("st_app/", "model", "code", "artist_mapping.json"), "r"
    ) as fp:
        artist_mapping = json.load(fp)
    return artist_mapping


def predict(img_filename: str) -> str:
    image = Image.open(img_filename)
    # return str(type(image))
    artist_mapping = get_artist_dict()
    model = get_model()
    tensor_input = IMAGE_TRANSFORMS(image)
    tensor_input = tensor_input.unsqueeze(0)
    logits = model(tensor_input)
    with torch.no_grad():
        prediction = int(torch.argmax(logits))
    str_prediction = str(prediction)
    return artist_mapping[str_prediction]


def predict_on_image(img):
    artist_mapping = get_artist_dict()
    model = get_model()
    tensor_input = IMAGE_TRANSFORMS(img)
    tensor_input = tensor_input.unsqueeze(0)
    logits = model(tensor_input)
    with torch.no_grad():
        prediction = int(torch.argmax(logits))
    str_prediction = str(prediction)
    return artist_mapping[str_prediction]


def main():
    page_config()
    selection = st.selectbox(
        "How do you want to select an image?",
        ["I want to use an already uploaded image", "I want to upload my own image"],
        index=0,
    )
    if selection == "I want to use an already uploaded image":
        img_filename = load_image_selection()
    else:
        img = st.file_uploader(
            "Upload your magic card image'",
            accept_multiple_files=False,
            type=["jpg"],
        )
        if img is not None:
            with open("./image.jpg", "wb") as f:
                f.write(img.getvalue())
            img_filename = "./image.jpg"

    if st.button(label="Run the model on the image"):
        st.write(f"The model predicts that the art is by {predict(img_filename)}")
    else:
        pass


if __name__ == "__main__":
    main()
