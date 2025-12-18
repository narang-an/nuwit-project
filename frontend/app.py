import streamlit as st
import requests

# API_BASE = "http://localhost:5000" #Flask backend URL
API_BASE = "http://127.0.0.1:5000" # flask dev server


st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Upload Clothes", "View Closet", "Build Outfit", "Saved Outfits"])

if page == "Home":
    st.title("Welcome to Your CLoset!")
    st.write("Upload your clothes and create outfits on your avatar")
    
elif page == "Upload Clothes":
    st.title("Upload Clothes")
    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
    category = st.selectbox("Select Category", ["Top", "Bottom", "Shoes", "Accessory"])
    
    if uploaded_file is not None:

        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
        
        if st.button("Save"):

            try:
                #build multipart/form-data paload:
                files = {
                    # (filename, fileobj, mimetype)
                    "file": (uploaded_file.name, uploaded_file, uploaded_file.type or "application/octet-stream")
                }
                data = {"category": category}

                resp = requests.post(f"{API_BASE}/uploads", files=files, data=data, timeout=20)

                if resp.ok:
                    result = resp.json()
                    if result.get("success"):
                        st.success(f"Uploaded: {result['filename']}")
                    else:
                        st.error(f"Upload 1 failed: {result.get('error', 'Unknown error')}")

                else:
                    st.error(f"Upload 2 failed: HTTP {resp.status_code}")
                
            except Exception as e:
                st.error(f"Upload failed: {str(e)}")


elif page == "View Closet":
    st.title("Your Closet")
    cats = ["Top", "Bottom", "Shoes", "Accessory"]

    for cat in cats:
        st.header(cat)
        try:
            resp = requests.get(f"{API_BASE}/get_clothes", params={"category": cat}, timeout=20)
            if not resp.ok:
                st.error(f"Failed to fetch {cat}: {resp.status_code}")
                continue

            files = resp.json().get("files", [])
            if not files:
                st.caption("No items in this category yet.")
            else:
                cols = st.columns(4) #creates one row with 4 equal-width columns
                for i, fname in enumerate(files):
                    img_url = f"{API_BASE}/uploads/{fname}"
                    with cols[i % 4]: #cycle through the 4 columns
                        st.image(img_url, width=150)
        except Exception as e:
            st.error(f"Error fetching {cat}: {str(e)}")

elif page == "Build Outfit":
    st.title("Build Your Outfit")
    st.write("Feature coming soon: drag and drop clothes onto your avatar")

elif page == "Saved Outfits":
    st.title("Saved Outfits")
    st.write("Feature coming soon: view and manage your saved outfits")


