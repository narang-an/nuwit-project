import streamlit as st
import requests
from datetime import datetime
from urllib.parse import quote

# API_BASE = "http://localhost:5000" #Flask backend URL
API_BASE = "http://127.0.0.1:5001" # flask dev server

st.set_page_config(layout="wide")
st.markdown("""
    <style>
    .stApp {
    background-color: #D9F0FF;
    }
    </style>
    """, unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "Home"

query_params = st.query_params
if "page" in query_params:
    st.session_state.page = query_params["page"]


# top navigation bar code
def render_navbar():
    pages = ["Home", "Upload Clothes", "View Closet", "Build Outfit", "Saved Outfits"]
    cols = st.columns(len(pages))

    for col, page_name in zip(cols, pages):
        with col:
            is_active = st.session_state.page == page_name

            if st.button(page_name, use_container_width=True, key=page_name):
                st.session_state.page = page_name
                st.rerun()

            if is_active:
                st.markdown(
                    "<div style='text-align:center; margin-top:0;'><hr style='border:3px solid #FF4B4B; width:80%; margin:auto'></div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    "<div style='text-align:center; margin-top:0;'><hr style='border:0px; width:80%; margin:auto'></div>",
                    unsafe_allow_html=True
                )

page = st.session_state.page

if page == "Home":
    st.markdown("<h1 style='text-align: center;'>Welcome to Your Virtual Closet!</h1>", unsafe_allow_html=True)
    st.write("")
    st.write("")

#home page buttons
    cols = st.columns(4)

    pages = {
        "Upload Clothes": "https://cdn-icons-png.flaticon.com/512/126/126477.png",
        "View Closet": "https://cdn-icons-png.flaticon.com/512/148/148466.png",
        "Build Outfit": "https://cdn-icons-png.flaticon.com/512/817/817214.png",
        "Saved Outfits": "https://cdn-icons-png.flaticon.com/512/1077/1077035.png"
    }

    for col, (page, img) in zip(cols, pages.items()):
        with col:
            if st.button(page, use_container_width=True):
                st.session_state.page = page
                st.rerun()

            st.markdown(
            f"""
            <div style="
                cursor: pointer;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 10px rgba(0,0,0,0.15);
            ">
                <img src="{img}" style="width:100%;">
                <div style="text-align:center; font-weight: 600; padding:8px;">
                {page}
                </div>
            </div>
            """,
            unsafe_allow_html=True
            )

        st.write("")
#weather

    city_coords = {
        "New York": (40.7128, -74.0060),
        "Boston": (42.3601, -71.0589)
    }

    city = st.selectbox("Select your city", list(city_coords.keys()))
    lat, lon = city_coords[city]

    def get_nws_forecast(lat, lon):
        headers = {"User-Agent": "my-closet-app"}
        try:

            points_url = f"https://api.weather.gov/points/{lat},{lon}"
            response = requests.get(points_url, headers=headers, timeout=10)
            response.raise_for_status()
            points_data = response.json()

            wfo = points_data["properties"]["gridId"]
            x = points_data["properties"]["gridX"]
            y = points_data["properties"]["gridY"]

            forecast_url = f"https://api.weather.gov/gridpoints/{wfo}/{x},{y}/forecast"
            forecast_resp = requests.get(forecast_url, headers=headers, timeout=10)
            forecast_resp.raise_for_status()
            forecast_data = forecast_resp.json()

            periods = forecast_data.get("properties", {}).get("periods", [])
            if not periods:
                return {"error": "No data available"}

            first = periods[0]
            return{
                "name": first.get("name", "N/A"),
                "temperature": first.get("temperature", "N/A"),
                "unit": first.get("temperatureUnit", "N/A"),
                "forecast" : first.get("detailedForecast", "No detailed"),
                "icon": first.get("icon", None),
            }
        except Exception as e:
            return {"error": str(e)}

    with st.spinner("Fetching weather data..."):
        weather = get_nws_forecast(lat, lon)

    if "error" in weather:
        st.error(f"Could not fetch weather data for {weather['error']}")
    else:
        col1, col2 = st.columns([2, 2])
        with col1:

            st.markdown("<h3 style='text-align:center'>Today's Weather</h3>", unsafe_allow_html=True)

            st.markdown(
                f"""
                <div style="
                border: 2px solid;
                border-radius: 5px;
                padding: 20px;
                text-align: center;
                background-color:;
                
                <h4 style='text-align:center'>{city} - {weather['name']} {weather['temperature']} {weather['unit']}</h4>
                
                
                <p> {weather['forecast']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        #Recommended Outfit
        with col2:
            st.markdown("<h3 style='text-align:center'>Recommended Outfit</h3>", unsafe_allow_html=True)

            resp = requests.get(f"{API_BASE}/get_outfits", timeout=10)
            outfits = resp.json().get("outfits", []) if resp.ok else []

            def choose_outfit(weather, outfits):
                if not outfits:
                    return None

                temp = weather.get("temperature", 70)

                if temp < 50:
                    return outfits[0]
                elif temp > 75:
                    return outfits[-1]
                else:
                    return outfits[len(outfits)//2]

            suggested = choose_outfit(weather, outfits)
            if suggested:

                resp = requests.get(
                    f"{API_BASE}/get_outfit_items",
                    params={"outfit_id": suggested["id"]},
                    timeout=10)
                items = resp.json().get("items", {}) if resp.ok else {}

                cols = st.columns(4)
                for i, category in enumerate(["Top", "Bottom", "Shoes", "Accessory"]):
                    with cols[i]:
                        st.markdown(f"**{category}**", unsafe_allow_html=True)
                        for entry in items.get(category, []):
                            st.image(f"{API_BASE}/uploads/{entry['filename']}", use_container_width=True)


    st.write("")
    st.write("")


    
elif page == "Upload Clothes":
    render_navbar()
    st.markdown("------")
    st.title("Upload Clothes:")
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
    render_navbar()
    st.markdown("------")
    st.title("In Your Closet:")

    st.markdown("""
    <style>
    .closet-card {
        width: 100%;
        height: 320px;
        overflow: hidden;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        margin-bottom: 10px;
        transition: transform 0.2s ease, box-shadow: 0.2s ease;
    }
    
    .closet-card img{
        width: 100%;
        height: 320px;
        object-fit: cover;
    }
    
    .closet-card:hover{
        transform: scale(1.08);
        box-shadow: 0 8px 2-px rgba(0,0,0,0.35);
        border: 2px solid #FF4B4B;
        z-index: 10;
        position: relative;
    }
    </style>
    """, unsafe_allow_html=True)


    tabs = st.tabs(["Tops", "Bottoms", "Shoes", "Accessories"])

    cat_map = {
        "Tops": "Top",
        "Bottoms": "Bottom",
        "Shoes": "Shoes",
        "Accessories": "Accessory",
    }

    for tab_label, tab in zip(cat_map.keys(), tabs):
        with tab:
            cat = cat_map[tab_label]

            try:
                resp = requests.get(
                    f"{API_BASE}/get_clothes",
                    params={"category": cat},
                    timeout=10
                )
                files = resp.json().get("files", []) if resp.ok else []

            except Exception as e:
                st.error(f" Error fetching {cat}: {str(e)}")
                files = []

            if not files:
                st.info("No items yet.")
                continue

            cols = st.columns(5)
            for i, fname in enumerate(files):
                with cols[i % 5]:
                    st.markdown(f"""
                    <div class='closet-card'>
                        <img src="{API_BASE}/uploads/{fname}">>,
                    </div>
                    """, unsafe_allow_html=True)

elif page == "Build Outfit":
    render_navbar()
    st.markdown("------")
    st.title("Build Your Outfit:")

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

    if "outfit_selections" not in st.session_state:
        st.session_state.outfit_selections = {cat: [] for cat in categories}

    st.markdown("""
    <style>
    .item-card {
        width: 100%;
        height: 300px;
        overflow: hidden;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        margin-bottom: 10px;
        transition: transform 0.2s ease, box-shadow: 0.2s ease;
        cursor: pointer;
    }
    .item-card img{
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .item-card:hover{
        transform: scale(1.08);
        box-shadow: 0 8px 2-px rgba(0,0,0,0.35);
    }
    .selected {
        border: 3px solid #FF4B4B;
    }
    </style>
    """, unsafe_allow_html=True)

    tabs = st.tabs(categories)

    for tab_label, tab in zip(categories, tabs):
        with tab:
            files = grouped_options[tab_label]
            if not files:
                st.info(f"No {tab_label} items yet.")
                continue

            cols = st.columns(5)
            for i, fname in enumerate(files):
                with cols[i % 5]:
                    selected_class = "selected" if fname in st.session_state.outfit_selections[tab_label] else ""

                    clicked = st.button("", key=f"{tab_label}_{fname}")
                    if clicked:
                        if fname in st.session_state.outfit_selections[tab_label]:
                            st.session_state.outfit_selections[tab_label].remove(fname)
                        else:
                            st.session_state.outfit_selections[tab_label].append(fname)

                    st.markdown(f"""
                        <div class='item-card {selected_class}'>
                        <img src="{API_BASE}/uploads/{fname}">
                        </div>
                        """, unsafe_allow_html=True)

    # outfit preview
    st.subheader("Outfit Preview")
    preview_cols = st.columns(4)
    for i, cat in enumerate(categories):
        with preview_cols[i]:
            st.markdown(f"**{cat}**")
            for fname in st.session_state.outfit_selections[cat]:
                st.image(f"{API_BASE}/uploads/{fname}", use_container_width=True)
            if not st.session_state.outfit_selections[cat]:
                st.caption("No items selected.")

    # save outfit
    if "default_outfit_name" not in st.session_state:
        st.session_state["default_outfit_name"] = "Outfit_" + datetime.now().strftime("%Y%m%d-%H%M%S")

    default_name = st.session_state["default_outfit_name"]

    with st.form("save_outfit_form", clear_on_submit=False):
        outfit_name = st.text_input("Outfit Name", value=default_name, key="outfit_name_input")
        submit = st.form_submit_button("Save Outfit")

        if submit:
            if not any(st.session_state.outfit_selections.values()):
                st.error("Please select at least one clothing item before saving.")
            else:
                name_to_save = (outfit_name or "").strip() or default_name
                payload = {
                    "outfit_name": name_to_save,
                    "clothing_items": st.session_state.outfit_selections
                }
                try:
                    with st.spinner("Saving Outfit..."):
                        resp = requests.post(f"{API_BASE}/save_outfit", json=payload, timeout=20)
                        result = resp.json() if resp.ok else None

                    if resp.ok and result and result.get("success"):
                        returned_name = result.get("outfit_name", name_to_save)
                        st.success(f"Outfit saved! ID # {result['outfit_id']} - {returned_name}")
                        st.session_state["default_outfit_name"] = "Outfit_" + datetime.now().strftime("%Y%m%d-%H%M%S")

                        st.session_state.outfit_selections = {cat: [] for cat in categories}
                    else:
                        msg = (result.get("error") if result else resp.text) or "Unknown error"
                        st.error(f"Failed to save outfit: {msg}")
                except Exception as e:
                    st.error("Error contacting backend.")
                    st.exception(e)
    
elif page == "Saved Outfits":
    render_navbar()
    st.markdown("------")
    st.title("Saved Outfits:")

    st.markdown("""
    <style>
    
    div[data-testid="stVerticleBlock"]:has(.outfit-card-anchor):hover {
        transform: translateY(-4px);
        box-shadow: 0 14px 30px rgba(0,0,0,0.18);
    }
    
    div[data-testid="stVerticleBlock"]:has(.outfit-card-anchor):hover {
        transform: translateY(-4px);
        box-shadow: 0 14px 30px rgba(0,0,0,0.18);
    }
    
    .image-wrapper {
        position: relative;
        width: 100%;
        aspect-ratio: 1 / 1;
        overflow: hidden;
        border-radius: 12px;
    }
    
    .image-wrapper img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }
    
    .category-placeholder {
        height: 100%;
        background: #f3f4f6;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #999;
        font-size: 12px
        border-radius: 12px;
    }
    
    .extra-badge {
        position: absolute;
        top: 6px;
        right: 6px;
        background: #4a6cf7;
        color: white;
        font-size: 10px;
        padding: 2px 6px;
        border-radius: 12px;
        font-weight: 600;
    }
    
    .outfit-title {
        text-align: center;
        font-weight: 600;
        font-size: 14px;
        margin-top: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    #getting saved outfits

    try:
        resp = requests.get(f"{API_BASE}/get_outfits", timeout=20)
        data = resp.json() if resp.ok else {}
        outfits = data.get("outfits", [])
    except Exception as e:
        outfits = []
        st.error(f"Error getting outfits: {e}")

    if not outfits:
        st.info("No saved outfits yet.")
    else:
        from urllib.parse import quote
        import unicodedata
        categories = ["Top", "Bottom", "Shoes", "Accessory"]

        for row_start in range(0, len(outfits), 3):
            row_outfits = outfits[row_start:row_start + 3]
            cols = st.columns(len(row_outfits), gap="small")

            for col, outfit in zip(cols, row_outfits):
                with col:
                    st.markdown("<div class='outfit-card-anchor'></div>", unsafe_allow_html=True)
                    outfit_id = outfit["id"]
                    outfit_name = outfit.get("outfit_name") or f"Outfit_{outfit_id}"

                    st.markdown(f"<div class='outfit-title'>{outfit_name}</div>", unsafe_allow_html=True)

                    try:
                        resp2 = requests.get(
                            f"{API_BASE}/get_outfit_items",
                            params={"outfit_id": outfit_id},
                            timeout=20
                        )
                        data2 = resp2.json() if resp2.ok else {}
                        items_by_category = data2.get("items", {})
                    except Exception as e:
                        items_by_category = {}


                    mini_cols = st.columns(2)
                    for i, cat in enumerate(categories):
                        with mini_cols[i % 2]:
                            cat_items = items_by_category.get(cat, [])

                            if cat_items:
                                item = cat_items[0]
                                fname = item["filename"]
                                img_path = f"{API_BASE}/uploads/{quote(fname, safe='')}"

                                badge_html = ""

                                if cat == "Accessory" and len(cat_items) > 1:
                                    badge_html = f"<div class='extra-badge'>+{len(cat_items)-1}</div>"

                                st.markdown(f"""<div class='image-wrapper'><img src='{img_path}'>{badge_html}</div>""", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div class='category-placeholder'>{cat}</div>", unsafe_allow_html=True)



