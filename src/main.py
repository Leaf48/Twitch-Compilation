import os
import shutil
import streamlit as st
from lib.utils_ import get_timestamp
from lib.twitch.clips import get_clips, render_comment, download_clip
from lib.clip import merge_video_with_comment_and_add_title, add_title_to_video
from lib.streamlit_.html import render_twitch_embed
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

st.divider()

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
    st.session_state.streamers = [
        # "dmf_kyochan",
        # "dasoku_aniki",
        # "yuyuta0702",
        # "turuokamonohashi",
        # "kokujintv",
        # "kato_junichi0817",
        # "hanjoudesu",
        # "nekoko88",
        # "bakumatsu_shishi",
        # "myakkomyako",
        # "kosuke_saiore",
    ]
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

    if font_file is not None:
        st.session_state.font_path = os.path.join(
            st.session_state.workdir, font_file.name
        )
        with open(st.session_state.font_path, "wb") as f:
            f.write(font_file.getbuffer())


# ? Add streamers
def add_streamer():
    if st.session_state.streamer_input:
        st.session_state.streamers.append(st.session_state.streamer_input)
        st.session_state.streamer_input = ""


st.text_input("Streamer", key="streamer_input", on_change=add_streamer)


# ? Show and edit streamers
st.session_state.streamers_available = st.multiselect(
    "Streamers",
    options=st.session_state.streamers,
    default=st.session_state.streamers,
)


# Search clips from each streamers
def search():
    st.session_state.all_clips = []

    for i in st.session_state.streamers_available:
        clips = get_clips(i, st.session_state.view_threshold, st.session_state.filter)
        st.session_state.all_clips.extend(clips)

    unique_clips = {}
    for clip in st.session_state.all_clips:
        unique_clips[clip["slug"]] = clip

    st.session_state.all_clips = list(unique_clips.values())

    st.session_state.all_clips = sorted(
        st.session_state.all_clips, key=lambda x: x["view"], reverse=True
    )


st.button(
    "Search", disabled=len(st.session_state.streamers_available) == 0, on_click=search
)

# ? Show clips
if st.session_state.all_clips:
    st.session_state.all_clips = [
        i for i in st.session_state.all_clips if not i.get("remove", False)
    ]

    for n, i in enumerate(st.session_state.all_clips):
        st.divider()

        st.write(i["title"], f"| {i["view"]} views | {i["game"]} | {i["createdAt"]} |")

        if "order" not in i:
            i["order"] = n

        input_value = st.number_input(
            "order", key=f"order_{i['slug']}", step=1, value=i["order"]
        )

        if i["order"] != input_value:
            i["order"] = input_value

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

        render_twitch_embed(i["slug"])

st.divider()


# ? Download
def start_downloading():
    st.session_state.all_clips = [i for i in st.session_state.all_clips if i["use"]]

    # Reorder
    st.session_state.all_clips = sorted(
        st.session_state.all_clips, key=lambda x: x["order"]
    )

    progress_bar = st.progress(0, text="Downloading...")
    for n, i in enumerate(st.session_state.all_clips):
        i["clip_path"] = os.path.join(
            st.session_state.workdir,
            f"clip_{i["view"]}_{i["game"]}_{i["title"]}.mp4",
        )
        download_clip(i["slug"], i["clip_path"])

        progress_bar.progress(
            (n + 1) / len(st.session_state.all_clips),
            text=f"{n + 1} out of {len(st.session_state.all_clips)} have been done.",
        )


def start_merging():
    clips = [i for i in st.session_state.all_clips if i["use"]]

    progress_bar = st.progress(0, text="Rendering videos...")
    for n, i in enumerate(clips):
        # Render comments and merging a video with it
        if i["use_comment"]:
            i["comment_path"] = os.path.join(
                st.session_state.workdir,
                f"chat_{i["view"]}_{i["game"]}_{i["title"]}.mp4",
            )

            # Set output path
            i["output_path"] = os.path.join(
                st.session_state.workdir,
                f"output_{i["view"]}_{i["game"]}_{i["title"]}.mp4",
            )

            # When VOD is unavailable
            if render_comment(i["slug"], i["comment_path"]):
                merge_video_with_comment_and_add_title(
                    i["clip_path"],
                    i["comment_path"],
                    st.session_state.font_path,
                    i["title"],
                    i["output_path"],
                )
            else:
                add_title_to_video(
                    i["clip_path"],
                    st.session_state.font_path,
                    i["title"],
                    i["output_path"],
                )
        else:
            i["output_path"] = i["clip_path"]

        progress_bar.progress(
            (n + 1) / len(clips),
            text=f"{n + 1} out of {len(clips)} have been rendered.",
        )

    with st.status("Merging all videos..."):
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
        final_clip.write_videofile(st.session_state.output, codec="libx264")

    return st.session_state.output


if st.button(
    "Create Compilation",
    disabled=len(st.session_state.streamers_available) == 0,
):
    start_downloading()
    st.session_state.output = start_merging()
    st.video(st.session_state.output)
