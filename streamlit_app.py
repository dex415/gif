import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter, UnidentifiedImageError
import os
import tempfile
import imageio
import io
from moviepy.editor import ImageSequenceClip
from datetime import datetime
from streamlit_sortables import sort_items
import numpy as np
from moviepy.video.fx.all import fadeout

LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")

st.set_page_config(page_title="🧢 TWNTY-TWO MP4 Creator", layout="centered", page_icon="logo.png")

st.markdown("""
    <style>
    .main {background-color: #fff;}
    h1, h2, h3 {color: #111; font-family: 'Helvetica Neue', sans-serif;}
    .stButton>button {background-color: #111;color: white;border-radius: 8px;}
    </style>
""", unsafe_allow_html=True)

st.title("🧢 TWNTY-TWO MP4 Creator")

# --- Presets ---
preset = st.selectbox("🎛️ Choose a preset", ["MP4 (Short Reel)", "MP4 (Longer Reel)", "Custom"])

# --- Upload Section ---
st.subheader("Upload Images")
uploaded_files = st.file_uploader("Drag and drop or browse to upload images", accept_multiple_files=True, type=["png", "jpg", "jpeg"], label_visibility="visible", key="uploader")
st.markdown("---")

# --- Preset Handling ---
if preset == "Custom":
    duration = st.slider("Frame display time (seconds)", min_value=0.5, max_value=5.0, value=1.5, step=0.1)
    output_format = "MP4"
    add_watermark = st.checkbox("Add TWNTY-TWO logo watermark", value=False)
else:
    if preset == "MP4 (Short Reel)":
        duration = 1.5
        add_watermark = True
    elif preset == "MP4 (Longer Reel)":
        duration = 2.2
        add_watermark = True
    output_format = "MP4"

# --- Export Options ---
st.subheader("Export Options")
repeat_all = st.checkbox("Repeat full animation once (MP4)", value=False)
fade_last = st.checkbox("Fade out at end of export (MP4 only)")
fade_duration = st.slider("Fade duration (seconds)", 0.5, 3.0, 1.0, step=0.1, key="fade_duration_slider")

# --- Handle Uploaded Files ---
if uploaded_files:
    file_dict = {}
    for file in uploaded_files:
        try:
            img = Image.open(file)
            img.load()
            file.seek(0)
            file_dict[file.name] = file
        except Exception:
            st.warning(f"Skipping {file.name}: not a valid image.")

    if not file_dict:
        st.error("No valid images uploaded. Please check your files.")
        st.stop()

    st.markdown("**Drag to reorder your images:**")
    ordered_filenames = sort_items(list(file_dict.keys()))

    if st.button("Create Output"):
        with tempfile.TemporaryDirectory() as tmpdir:
            images = []
            for fname in ordered_filenames:
                file = file_dict[fname]
                img_path = os.path.join(tmpdir, file.name)
                file.seek(0)
                with open(img_path, "wb") as f:
                    f.write(file.read())
                try:
                    img = Image.open(img_path).convert("RGB")
                except UnidentifiedImageError:
                    st.error(f"Unable to open image: {file.name}. Please make sure it's a valid PNG or JPG.")
                    continue

                # Add watermark if enabled
                if add_watermark and os.path.exists(LOGO_PATH):
                    try:
                        logo = Image.open(LOGO_PATH).convert("RGBA")
                        base_width = img.width
                        logo_width = int(base_width * 0.15)
                        w_percent = logo_width / float(logo.size[0])
                        logo_height = int(float(logo.size[1]) * w_percent)
                        logo = logo.resize((logo_width, logo_height), Image.LANCZOS)
                        watermarked = Image.new("RGBA", img.size, (255, 255, 255, 255))
                        watermarked.paste(img.convert("RGBA"), (0, 0))
                        pos_x = img.width - logo_width - 4
                        pos_y = img.height - logo_height - 2
                        watermarked.paste(logo, (pos_x, pos_y), logo)
                        img = watermarked.convert("RGB")
                    except Exception:
                        pass

                images.append(img)

            if not images:
                st.error("No valid images were processed. Please upload at least one supported file.")
                st.stop()

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_path = os.path.join(tmpdir, f"twnty_two_hat_{timestamp}.mp4")

            # Export MP4
            images_np = [np.array(img.convert("RGB")) for img in images * 2] if repeat_all else [np.array(img.convert("RGB")) for img in images]
            clip = ImageSequenceClip(images_np, fps=1 / duration)
            if fade_last:
                clip = fadeout(clip, duration=fade_duration)
            clip.write_videofile(output_path, codec="libx264", audio=False, verbose=False, logger=None)

            st.success(f"{output_format} created!")
            st.video(output_path)

            with open(output_path, "rb") as f:
                st.download_button(f"Download {output_format}", f, file_name=os.path.basename(output_path), mime="video/mp4")

st.markdown("---")
st.markdown("<div style='text-align: center; font-size: 0.9rem; color: #777;'>Made by <a href='https://masvida.agency' target='_blank' style='color: #777; text-decoration: none;'>🏵 Más Vida Agency 🏵 for TWNTY-TWO®️ </a></div>", unsafe_allow_html=True)
