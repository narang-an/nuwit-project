import streamlit as st
from PIL import Image
import os

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# page = st.sidebar.selectbox("Navigate", ["Home", "Upload Clothes", "View Closet", "Build Outfit"])

if "page" not in st.session_state:
    st.session_state.page = "Home"

col1, col2, col3, col4 = st.columns(4)
if col1.button("Home"):
    st.session_state.page = "Home"
if col2.button("Upload Clothes"):
    st.session_state.page = "Upload Clothes"
if col3.button("View Closet"):
    st.session_state.page = "View Closet"
if col4.button("Build Outfit"):
    st.session_state.page = "Build Outfit"

page = st.session_state.page

if page == "Home":
    st.title("Welcome to Your CLoset!")
    st.write("Upload your clothes and create outfits on your avatar")
    
elif page == "Upload Clothes":
    st.title("Upload Clothes")
    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
    category = st.selectbox("Select Category", ["Top", "Bottom", "Shoes", "Accessory"])
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded Image")
        if st.button("Save"):
            file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
            img.save(file_path)
            st.success("Image saved!")

elif page == "View Closet":
    st.title("Your Closet")
    files = os.listdir(UPLOAD_DIR)
    if files:
        for f in files:
            st.image(os.path.join(UPLOAD_DIR, f), width=150)
    else:
        st.write("No clothes uploaded yet.")

elif page == "Build Outfit":
    st.title("Build Your Outfit")
    st.write("Feature coming soon: drag and drop clothes onto your avatar")



