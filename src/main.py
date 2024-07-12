import os
import subprocess
from twitch import Twitch
import streamlit as st
from moviepy.editor import (
    CompositeVideoClip,
    VideoFileClip,
    vfx,
    concatenate_videoclips,
)


def downloadVideo(url: str, output_title: str) -> None:
    cmd = ["streamlink", url, "best", "-f", "--output", output_title + ".mp4"]
    subprocess.run(cmd)


if "checkedClips" not in st.session_state:
    st.session_state.checkedClips = []

if "clips" not in st.session_state:
    st.session_state.clips = []

if "compilation.mp4" not in st.session_state:
    st.session_state.output = ""

font_file = st.file_uploader("Upload a font file", type=["otf", "ttf"])
font_path = ""

if font_file is not None:
    # create re-encoded clips directory
    reencoded_dir = "reencoded_clips"
    os.makedirs(reencoded_dir, exist_ok=True)

    font_path = os.path.join(reencoded_dir, font_file.name)
    with open(font_path, "wb") as f:
        f.write(font_file.getbuffer())

streamer = st.text_input("Enter streamer")

if st.button("Download Clips"):
    t = Twitch(streamer=streamer)
    st.session_state.clips = t.getClips("LAST_DAY")
    clips = st.session_state.clips

    progress_bar = st.progress(0)

    for n, i in enumerate(clips):
        title = f'{i["view"]}_{i["genre"]}_{i["duration"]}'
        clips[n]["filename"] = title + ".mp4"

        downloadVideo(i["url"], title)

        progress_bar.progress((n + 1) / len(clips))

st.write("Downloaded Clips:")
for clip in st.session_state.clips:
    key = clip["slug"]

    clip_title = f'{clip["title"]} ({clip["view"]} views, {clip["genre"]})'

    if st.checkbox(clip_title, key=key):
        if clip not in st.session_state.checkedClips:
            st.session_state.checkedClips.append(clip)
    else:
        if clip in st.session_state.checkedClips:
            st.session_state.checkedClips.remove(clip)

    new_title = st.text_input(
        "Enter if you need to change title", value=clip["title"], key=key + "text_input"
    )
    clip["title"] = new_title
    st.video(clip["filename"])


if st.button("Create Compilation"):
    st.session_state.output = "compilation.mp4"

    progress_bar = st.progress(0)
    # ? Reencode and put text
    with open("list.txt", "w") as f:
        _temp = []

        for i, clip in enumerate(st.session_state.checkedClips):
            reencoded_clip = os.path.join(reencoded_dir, f"clip_{i}.mp4")
            output_with_text = os.path.join(reencoded_dir, f"clip_with_text_{i}.mp4")

            clip["output_file"] = output_with_text
            _temp.append(clip)

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                clip["filename"],
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                reencoded_clip,
            ]
            subprocess.run(cmd)

            progress_bar.progress(
                (i * 2 + 1) / (len(st.session_state.checkedClips) * 2)
            )

            cmd_text = [
                "ffmpeg",
                "-y",
                "-i",
                reencoded_clip,
                "-vf",
                f"drawtext=fontfile='{font_path}':text='{clip["title"]}':x=(w-text_w)-70:y=(h-text_h)-10:fontsize=64:fontcolor=white",
                output_with_text,
            ]
            subprocess.run(cmd_text)

            f.write(f"file '{output_with_text}'\n")

            progress_bar.progress(
                (i * 2 + 2) / (len(st.session_state.checkedClips) * 2)
            )

        st.session_state.checkedClips = _temp

    clips = []
    crossfade_duration = 1

    # 動画クリップを読み込んでリストに追加
    for i in st.session_state.checkedClips:
        clips.append(VideoFileClip(i["output_file"]))

    # すべてのクリップにクロスフェードを適用
    for j in range(1, len(clips)):
        clips[j - 1] = clips[j - 1].crossfadeout(crossfade_duration)
        clips[j] = clips[j].crossfadein(crossfade_duration)

    # クリップを結合
    final_clip = concatenate_videoclips(clips, method="compose")

    # 結果をファイルに書き出す
    final_clip.write_videofile(st.session_state.output)


if st.session_state.output:
    st.write("Generated Compilation")
    st.video(st.session_state.output)
