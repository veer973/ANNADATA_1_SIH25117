import streamlit as st
import requests
import cv2
import pandas as pd
import time
import os
import random

# --- Configuration ---
FASTAPI_URL = "http://127.0.0.1:8000"
RESULT_CSV = "results/result.csv"
MAX_FPS = 15  # Maximum frames per second
PROCESS_INTERVAL = 3  # Seconds between processing frames for AI
FRAME_WIDTH = 900  # Target width for video frame

# --- Page Setup ---
st.set_page_config(
    page_title="Smart Agriculture Monitor",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar for Fertility Prediction ---
st.sidebar.title("Soil Fertility Analysis")
st.sidebar.markdown("Adjust the sliders to match the soil sensor readings and predict fertility.")

n_value = st.sidebar.slider("Nitrogen (N)", min_value=6, max_value=383, value=150, help="Range: 6-383")
p_value = st.sidebar.slider("Phosphorus (P)", min_value=3, max_value=125, value=50, help="Range: 3-125")
k_value = st.sidebar.slider("Potassium (K)", min_value=11, max_value=887, value=200, help="Range: 11-887")
ph_value = st.sidebar.slider("Soil pH", min_value=1.0, max_value=12.0, value=7.0, step=0.1, help="Range: 1.0-12.0")
ec_value = st.sidebar.slider("Electrical Conductivity (EC)", min_value=0.1, max_value=0.95, value=0.5, step=0.01, help="Range: 0.1-0.95")

if st.sidebar.button("Predict Soil Fertility", use_container_width=True):
    with st.sidebar:
        with st.spinner("Analyzing..."):
            try:
                payload = {"n": n_value, "p": p_value, "k": k_value, "ph": ph_value, "ec": ec_value}
                response = requests.post(f"{FASTAPI_URL}/predict_fertility/", json=payload, timeout=5)
                if response.status_code == 200:
                    result = response.json()
                    fertility_status = result.get("fertility", "Error")
                    st.metric("Fertility Status", fertility_status)
                else:
                    st.error("Failed to get prediction. Server might be busy.")
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {e}")

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .title-container {
        background-color: #2c3e50;
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
        background-color: #27ae60;
        color: white;
        border-radius: 5px;
        padding: 0.5rem;
    }
    .metric-container {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        font-weight: bold;
        font-size: 1.1rem;
        text-align: center;
        border: 3px solid transparent;
    }
    /* Make Download button styled */
    div.stDownloadButton > button {
        background-color: #2980b9;  /* Blue button */
        color: white;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    div.stDownloadButton > button:hover {
        background-color: #1f618d; /* Darker on hover */
    }
     
    </style>
""", unsafe_allow_html=True)


# --- Helper for Status Colors ---
def get_status_html(label, value):
    # Default styling
    color = "#2c3e50"
    border = "#bdc3c7"
    bg = "#ecf0f1"  # light gray default

    # Conditions for coloring
    if value in ["Healthy", "Not Detected"]:
        color, border, bg = "#27ae60", "#27ae60", "#d4efdf"  # Green
    elif value in ["N/A", "No Leaf Detected"]:
        color, border, bg = "#f39c12", "#f39c12", "#fdebd0"  # Orange/Yellow
    elif value in ["Detected", "Brown_Spot", "Blight", "Rust", "High Fertility", "Medium Fertility", "Low Fertility"]:
        color, border, bg = "#e74c3c", "#e74c3c", "#f5b7b1"  # Red

    # Return styled HTML
    return f"""
    <div class="metric-container" style="
        border: 2px solid {border};
        color: {color};
        background-color: {bg};
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
        font-weight: bold;
    ">
        {label}: {value}
    </div>
    """

# --- Title ---
st.markdown(
    """
    <div class="title-container">
        <h1>🌱 Smart Agriculture Monitoring Dashboard</h1>
        <p style='font-size: 1.2rem; margin-bottom: 0;'>Real-time Plant Health Analysis System</p>
    </div>
    """, 
    unsafe_allow_html=True
)

# --- Session State ---
if "ip_url" not in st.session_state:
    st.session_state.ip_url = ""
if "monitoring" not in st.session_state:
    st.session_state.monitoring = False
if "last_leaf_result" not in st.session_state:
    st.session_state.last_leaf_result = "N/A"
if "last_weed_result" not in st.session_state:
    st.session_state.last_weed_result = "N/A"

# --- Camera Input ---
st.markdown("""<div class="status-heading">Camera Settings</div>""", unsafe_allow_html=True)
col_url, col_button = st.columns([3, 1])
with col_url:
    st.session_state.ip_url = st.text_input(
        "Enter IP camera URL",
        st.session_state.ip_url,
        placeholder="Enter IP camera URL",
        label_visibility="collapsed"
    )
with col_button:
    if st.button("Start" if not st.session_state.monitoring else "Stop", use_container_width=True):
        st.session_state.monitoring = not st.session_state.monitoring

# --- Layout ---
col1, col2 = st.columns([3, 1], gap="small")  # was [2,1]

with col1:
    st.markdown("""<div class="status-heading">Live Feed</div>""", unsafe_allow_html=True)
    placeholder_video = st.empty()

with col2:
    st.markdown("""<div class="status-heading">System Status</div>""", unsafe_allow_html=True)
    leaf_placeholder = st.empty()
    weed_placeholder = st.empty()

    st.markdown("""<div class="status-heading">Analysis History</div>""", unsafe_allow_html=True)
    placeholder_table = st.empty()
    placeholder_button = st.empty()

# --- Monitoring Loop ---
if st.session_state.monitoring and st.session_state.ip_url:
    cap = cv2.VideoCapture(st.session_state.ip_url)
    if not cap.isOpened():
        st.error("Could not open video stream. Check URL and ensure the camera is active.")
        st.session_state.monitoring = False
    else:
        while st.session_state.monitoring:
            time.sleep(1 / MAX_FPS)
            ret, frame = cap.read()
            if not ret:
                st.warning("Connection to camera lost. Stopping.")
                st.session_state.monitoring = False
                break

            # Resize frame
            height, width = frame.shape[:2]
            if width > FRAME_WIDTH:
                scale = FRAME_WIDTH / width
                frame = cv2.resize(frame, (FRAME_WIDTH, int(height * scale)))

            placeholder_video.image(frame, channels="BGR")

            # Process frame periodically
            current_time = time.time()
            if current_time - st.session_state.get('last_process_time', 0) >= PROCESS_INTERVAL:
                st.session_state.last_process_time = current_time
                temp_frame_path = "results/temp_frame.jpg"
                cv2.imwrite(temp_frame_path, frame)

                try:
                    with open(temp_frame_path, "rb") as f:
                        leaf_res = requests.post(f"{FASTAPI_URL}/classify_leaf/", files={"file": f}, timeout=3)
                        if leaf_res.status_code == 200:
                            response_data = leaf_res.json()
                            leaf_detected = response_data.get("leaf_detected", False)
                            disease = response_data.get("disease", "N/A")

                            if not leaf_detected:
                                st.session_state.last_leaf_result = "No Leaf Detected"
                                st.session_state.last_weed_result = "N/A"
                            else:
                                st.session_state.last_leaf_result = disease

                                with open(temp_frame_path, "rb") as f:
                                    weed_res = requests.post(f"{FASTAPI_URL}/detect_weed/", files={"file": f}, timeout=3)
                                    if weed_res.status_code == 200:
                                        detected = weed_res.json().get("weed_detected", False)
                                        st.session_state.last_weed_result = "Detected" if detected else "Not Detected"
                        else:
                            st.session_state.last_leaf_result = "N/A"
                            st.session_state.last_weed_result = "N/A"
                except requests.exceptions.RequestException:
                    st.session_state.last_leaf_result = "N/A"
                    st.session_state.last_weed_result = "N/A"

            # --- Update UI ---
            leaf_placeholder.markdown(get_status_html("🍃Leaf Status", st.session_state.last_leaf_result), unsafe_allow_html=True)
            weed_placeholder.markdown(get_status_html("🌿Weed Status", st.session_state.last_weed_result), unsafe_allow_html=True)

            if os.path.exists(RESULT_CSV):
                unique_key = f"download_csv_button_{time.time_ns()//1000000}_{random.randint(0,1000)}"
                df_res = pd.read_csv(RESULT_CSV)
                df_display = df_res.tail(8).copy()

                placeholder_table.dataframe(
                    df_display,
                    width='stretch',
                    height=250,
                    hide_index=True
                )

                csv_data = df_res.to_csv(index=False).encode("utf-8")
                placeholder_button.download_button(
                    label="Download History",
                    data=csv_data,
                    file_name="analysis_results.csv",
                    mime="text/csv",
                    key=unique_key,
                    use_container_width=True
                )
    cap.release()
else:
    placeholder_video.info("Enter an IP Webcam URL and click 'Start Monitoring' to begin.")
