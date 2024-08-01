import streamlit as st


def render_twitch_embed(slug: str):
    twitch_embed_code = f"""
<iframe src="https://clips.twitch.tv/embed?clip={slug}&parent=localhost"
    frameborder="0"
    allowfullscreen="true"
    scrolling="no"
    height="378"
    width="620">
</iframe>
"""

    return st.components.v1.html(twitch_embed_code, height=378)
