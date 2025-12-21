import streamlit as st
import requests
from datetime import datetime

# API_BASE = "http://localhost:5000" #Flask backend URL
API_BASE = "http://127.0.0.1:5001" # flask dev server


st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Upload Clothes", "View Closet", "Build Outfit", "Saved Outfits"])

def delete_clothing_item(category: str, filename: str, force: bool = False) -> bool:
    try:
        params = {"category": category, "filename": filename, "force": str(force).lower()}
        resp = requests.delete(f"{API_BASE}/delete_clothing", params=params, timeout=15)
        if resp.status_code in (200, 204):
            st.success(f"Deleted: {filename}")
            return True
        elif resp.status_code == 409:
            data = resp.json()
            ids = data.get("outfit_ids", [])
            st.warning(f"'{filename}' is used in outfits: {ids}. Delete blocked. "
                       f"Click 'Force Delete' to remove it from those outfits.")
            return False
        else:
            try:
                msg = resp.json().get("error")
            except Exception:
                msg = resp.text
            st.error(f"Delete failed ({resp.status_code}): {msg}")
            return False
    except Exception as e:
        st.error(f"Delete failed: {e}")
        return False

def delete_outfit(outfit_id: int) -> bool:
    try:
        resp = requests.delete(f"{API_BASE}/delete_outfit", params={"outfit_id": outfit_id}, timeout=15)
        if resp.status_code in (200, 204):
            st.success(f"Outfit #{outfit_id} deleted.")
            return True
        elif resp.status_code == 404:
            st.error("Outfit not found.")
            return False
        else:
            try:
                msg = resp.json().get("error")
            except Exception:
                msg = resp.text
            st.error(f"Delete failed ({resp.status_code}): {msg}")
            return False
    except Exception as e:
        st.error(f"Delete failed: {e}")
        return False

if page == "Home":
    st.title("Welcome to Your CCloset!")
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
                cols = st.columns(4)

                for i, fname in enumerate(files):
                    img_url = f"{API_BASE}/uploads/{fname}"
                    with cols[i % 4]:
                        st.image(img_url, width=150)

                        # Keys for per-item state
                        confirm_key = f"confirm_{cat}_{fname}"
                        blocked_key = f"blocked_{cat}_{fname}"

                        # Delete button with two-click confirm
                        if st.button("Delete", key=f"del_{cat}_{fname}"):
                            if st.session_state.get(confirm_key, False):
                                ok = delete_clothing_item(cat, fname, force=False)
                                # If deletion succeeded, clear flags and rerun
                                if ok:
                                    st.session_state.pop(confirm_key, None)
                                    st.session_state.pop(blocked_key, None)
                                    # Streamlit >= 1.30
                                    st.rerun()
                                else:
                                    # Blocked: show Force Delete next render
                                    st.session_state[blocked_key] = True
                                    # Clear confirm so next click starts fresh
                                    st.session_state.pop(confirm_key, None)
                            else:
                                st.warning("Click 'Delete' again to confirm.")
                                st.session_state[confirm_key] = True

                        # Show Force Delete ONLY if a previous delete was blocked
                        if st.session_state.get(blocked_key, False):
                            if st.button("Force Delete", key=f"force_{cat}_{fname}"):
                                ok = delete_clothing_item(cat, fname, force=True)
                                if ok:
                                    st.session_state.pop(blocked_key, None)
                                    st.rerun()

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
        options = {f"#{o['id']} — {o.get('outfit_name') or '(unnamed)'}": o["id"] for o in outfits}
        label = st.selectbox("Choose an outfit to preview", list(options.keys()))
        selected_id = options[label]

        # Preview (your existing code)
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

        st.divider()
        # Confirmed delete
        del_confirm_key = f"confirm_outfit_{selected_id}"
        if st.button("Delete This Outfit"):
            if st.session_state.get(del_confirm_key, False):
                if delete_outfit(selected_id):
                    st.session_state.pop(del_confirm_key, None)
                    st.rerun()
            else:
                st.warning("Click delete again to confirm.")
                st.session_state[del_confirm_key] = True

