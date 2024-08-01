import streamlit as st
from sys import platform


def render_twitch_embed(slug: str):
    parent = "localhost" if platform == "darwin" else "192.168.1.137"
    twitch_embed_code = f"""
<iframe src="https://clips.twitch.tv/embed?clip={slug}&parent={parent}"
    frameborder="0"
    allowfullscreen="true"
    scrolling="no"
    height="378"
    width="620">
</iframe>
"""

    return st.components.v1.html(twitch_embed_code, height=378)
