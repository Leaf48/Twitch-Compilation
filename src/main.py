import os
import streamlit as st
from lib.utils_ import get_timestamp

# ? Static variables
if "workdir" not in st.session_state:
    st.session_state.workdir = None
if "font_path" not in st.session_state:
    st.session_state.font_path = None
if "streamers" not in st.session_state:
    st.session_state.streamers = []


# ? Create working directory
if st.session_state.workdir is None:
    st.session_state.workdir = os.path.join(f"wd_{get_timestamp()}")
    os.mkdir(st.session_state.workdir)

# ? Set font
if st.session_state.font_path is None:
    font_file = st.file_uploader("Upload a font file", type=["otf", "ttf"])
    font_path = ""

    if font_file is not None:
        font_path = os.path.join(st.session_state.workdir, font_file.name)
        with open(font_path, "wb") as f:
            f.write(font_file.getbuffer())


# ? Add streamers
def add_streamer():
    if st.session_state.streamer_input:
        st.session_state.streamers.append(st.session_state.streamer_input)
        st.session_state.streamer_input = ""  # 入力フィールドをクリア


st.text_input("Streamer", key="streamer_input", on_change=add_streamer)

st.write("Streamers")
st.text("\n".join(st.session_state.streamers))
