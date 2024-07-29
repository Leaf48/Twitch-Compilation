import os
import shutil
import streamlit as st
from lib.utils_ import get_timestamp
from lib.twitch.clips import get_clips, render_comment, download_clip
from lib.clip import merge_video_with_comment
from streamlit_sortables import sort_items
from moviepy.editor import (
    VideoFileClip,
    concatenate_videoclips,
)

# ! Cache control
st.write(f"Cache: {len([i for i in os.listdir("./") if i.startswith("wd_")])}")
if st.button("Remove cache"):
    dir = [i for i in os.listdir("./") if i.startswith("wd_")]
    for i in dir:
        shutil.rmtree(i)

# ? Static variables
if "view_threshold" not in st.session_state:
    st.session_state.view_threshold = 1000
if "filter" not in st.session_state:
    st.session_state.filter = "LAST_DAY"
if "workdir" not in st.session_state:
    st.session_state.workdir = None
if "font_path" not in st.session_state:
    st.session_state.font_path = None
if "streamers" not in st.session_state:
    st.session_state.streamers = []
if "streamers_available" not in st.session_state:
    st.session_state.streamers_available = []
if "all_clips" not in st.session_state:
    st.session_state.all_clips = []
if "output" not in st.session_state:
    st.session_state.output = None


st.session_state.view_threshold = st.slider(
    "View threshold",
    min_value=0,
    max_value=10000,
    value=st.session_state.view_threshold,
)

st.session_state.filter = st.selectbox(
    "Filter", ["LAST_DAY", "LAST_WEEK", "LAST_MONTH", "ALL_TIME"]
)


# ? Create working directory
if st.session_state.workdir is None:
    st.session_state.workdir = os.path.join(f"wd_{get_timestamp()}")
    os.mkdir(st.session_state.workdir)

# ? Set output path
if st.session_state.output is None:
    st.session_state.output = os.path.join(
        st.session_state.workdir, f"final_{get_timestamp()}.mp4"
    )

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
        st.session_state.streamer_input = ""


st.text_input("Streamer", key="streamer_input", on_change=add_streamer)


# ? Show and edit streamers
st.session_state.streamers_available = st.multiselect(
    "Streamers", options=st.session_state.streamers, default=st.session_state.streamers
)


# ? Download
def start_to_download():
    # st.session_state.all_clips = []
    for i in st.session_state.streamers_available:
        progress_bar = st.progress(0)
        clips = get_clips(i, st.session_state.view_threshold, st.session_state.filter)
        for n, j in enumerate(clips):
            if f"use_{j["slug"]}" in st.session_state:
                continue

            clip_output = os.path.join(
                st.session_state.workdir,
                f"clip_{j["view"]}_{j["game"]}_{j["title"]}.mp4",
            )
            download_clip(j["slug"], clip_output)

            # Setting
            j["clip_path"] = clip_output
            j["remove"] = False

            st.session_state.all_clips.append(j)
            progress_bar.progress((n + 1) / len(clips))
            # break
        progress_bar.empty()
        # break


if st.button(
    "Download",
    on_click=start_to_download,
    disabled=len(st.session_state.streamers_available) == 0,
):
    st.session_state.output = None


# ? Show clips
if st.session_state.all_clips:
    st.session_state.all_clips = [
        i for i in st.session_state.all_clips if not i.get("remove", False)
    ]

    clips_order = sort_items(
        [i["title"] for i in st.session_state.all_clips],
    )

    title_to_clip = {clip["title"]: clip for clip in st.session_state.all_clips}
    st.session_state.all_clips = [title_to_clip[title] for title in clips_order]

    for i in st.session_state.all_clips:
        st.write(i["title"], f"| {i["view"]} views | {i["game"]} |")
        i["title"] = st.text_input(
            "Title if needed", value=i["title"], key=f"title_{i["slug"]}"
        )
        i["use"] = st.checkbox("Include", key=f"use_{i["slug"]}")
        i["use_comment"] = st.checkbox(
            "Comment Overlay", key=f"use_comment_{i["slug"]}", value=True
        )
        if st.button("Remove", key=f"remove_{i["slug"]}"):
            i["remove"] = True
            st.rerun()

        st.video(i["clip_path"])

# Start merging
if st.button("Process"):
    clips = [i for i in st.session_state.all_clips if i["use"]]

    for i in clips:
        if i["use_comment"]:
            i["comment_path"] = os.path.join(
                st.session_state.workdir,
                f"chat_{i["view"]}_{i["game"]}_{i["title"]}.mp4",
            )
            render_comment(i["slug"], i["comment_path"])

            i["output_path"] = os.path.join(
                st.session_state.workdir,
                f"output_{i["view"]}_{i["game"]}_{i["title"]}.mp4",
            )
            merge_video_with_comment(
                i["clip_path"], i["comment_path"], i["output_path"]
            )
        else:
            i["output_path"] = i["clip_path"]

    # Merge all video with fade-inout
    clip_queue = []
    crossfade_duration = 1
    for i in clips:
        clip_queue.append(VideoFileClip(i["output_path"]))

    # Apply crossfade to all clips
    for j in range(1, len(clip_queue)):
        clip_queue[j - 1] = clip_queue[j - 1].crossfadeout(crossfade_duration)
        clip_queue[j] = clip_queue[j].crossfadein(crossfade_duration)

    # Merge clips
    final_clip = concatenate_videoclips(clip_queue, method="compose")

    # Write final result
    final_clip.write_videofile(st.session_state.output)

if os.path.exists(st.session_state.output):
    st.write("Final Result")
    st.video(st.session_state.output)
