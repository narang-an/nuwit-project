import streamlit as st
import requests
from datetime import datetime

# API_BASE = "http://localhost:5000" #Flask backend URL
API_BASE = "http://127.0.0.1:5001" # flask dev server


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

    # 1) Categories & options container
    categories = ["Top", "Bottom", "Shoes", "Accessory"]
    grouped_options = {cat: [] for cat in categories}

    # 2) Fetch options per category from backend
    try:
        for cat in categories:
            resp = requests.get(f"{API_BASE}/get_clothes", params={"category": cat}, timeout=15)
            data = resp.json() if resp.ok else {}
            grouped_options[cat] = data.get("files", [])
    except Exception as e:
        st.error(f"Error fetching clothes: {e}")

    # 3) Multi-select per category
    st.subheader("Select items for your outfit")
    selections = {}
    cols = st.columns(4)
    for i, cat in enumerate(categories):
        with cols[i]:
            selections[cat] = st.multiselect(cat, grouped_options[cat], default=[])

    # 4) Simple preview (stacked by category)
    st.subheader("Outfit Preview")
    preview_cols = st.columns(4)
    for i, cat in enumerate(categories):
        with preview_cols[i]:
            st.markdown(f"**{cat}**")
            if selections[cat]:
                for fname in selections[cat]:
                    img_url = f"{API_BASE}/uploads/{fname}"
                    st.image(img_url, use_container_width=True)
            else:
                st.caption("No items selected")

    # 5) Save outfit (form)
    st.subheader("Save Outfit")

    # Stable default name (won't change every rerun)
    if "default_outfit_name" not in st.session_state:
        st.session_state["default_outfit_name"] = "Outfit_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    default_name = st.session_state["default_outfit_name"]

    with st.form("save_outfit_form", clear_on_submit=False):
        outfit_name = st.text_input(
            "Outfit Name:",
            value=default_name,  # show editable default value
            key="outfit_name_input"
        )

        submit = st.form_submit_button("Save Outfit")

        if submit:
            # Optional validation: require at least one selection
            if not any(selections.values()):
                st.error("Please select at least one clothing item before saving.")
            else:
                name_to_save = (outfit_name or "").strip() or default_name

                payload = {
                    "outfit_name": name_to_save,
                    "clothing_items": selections  # dict: {category: [filenames]}
                }

                try:
                    with st.spinner("Saving outfit..."):
                        resp = requests.post(f"{API_BASE}/save_outfit", json=payload, timeout=20)

                    # Safe JSON parsing
                    try:
                        result = resp.json()
                    except ValueError:
                        result = None

                    if resp.ok:
                        if result and result.get("success"):
                            returned_name = result.get("outfit_name", name_to_save)
                            st.success(f"Outfit saved! ID # {result['outfit_id']} — {returned_name}")

                            # Rotate a new default name for the next save (optional)
                            st.session_state["default_outfit_name"] = "Outfit_" + datetime.now().strftime("%Y%m%d_%H%M%S")
                        else:
                            msg = (result.get("error") if result else resp.text) or "Unknown error"
                            st.error(f"Failed to save outfit: {msg}")
                    else:
                        err_msg = (
                            result.get("error") if (result and isinstance(result, dict) and "error" in result)
                            else resp.text or f"HTTP {resp.status_code}"
                        )
                        st.error(f"Failed to save outfit: {err_msg}")

                except Exception as e:
                    st.error("Error contacting backend.")
                    st.exception(e)
    
elif page == "Saved Outfits":
    st.title("Saved Outfits")
    
    #fetch saved outfits
    try:
        resp = requests.get(f"{API_BASE}/get_outfits", timeout=15)
        data = resp.json() if resp.ok else {}
        outfits = data.get("outfits", [])
    except Exception as e:
        outfits = []
        st.error(f"Error fetching outfits: {e}")

    if not outfits:
        st.info("No saved outfits yet.")
    else:
        # Select an outfit to preview
        options = {f"#{o['id']} — {o.get('outfit_name') or '(unnamed)'}": o["id"] for o in outfits}
        label = st.selectbox("Choose an outfit to preview", list(options.keys()))
        selected_id = options[label]


        # Fetch items for that outfit
        try:
            resp2 = requests.get(f"{API_BASE}/get_outfit_items", params={"outfit_id": selected_id}, timeout=15)
            di = resp2.json() if resp2.ok else {}
            items = di.get("items", {})
        except Exception as e:
            items = {}
            st.error(f"Error fetching outfit items: {e}")

        st.subheader("Outfit Preview")
        cats = ["Top", "Bottom", "Shoes", "Accessory"]
        cols = st.columns(4)
        for i, cat in enumerate(cats):
            with cols[i]:
                st.markdown(f"**{cat}**")
                for entry in items.get(cat, []):
                    fname = entry["filename"]
                    st.image(f"{API_BASE}/uploads/{fname}", use_container_width=True)
