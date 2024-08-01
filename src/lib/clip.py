import subprocess


def merge_video_with_comment_and_add_title(
    video_path: str, comment_path: str, font_path: str, clip_title: str, output: str
):
    """Merge video with comment video

    Args:
        video_path (str): input path
        comment_path (str): comment path
        output (str): output path
    """

    # crop=width:height:x:y
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        comment_path,
        "-filter_complex",
        (
            "[1]crop=in_w:100:0:in_h-100,"
            "format=rgba,"
            "colorchannelmixer=aa=0.5[ov];"
            "[0][ov]overlay=W-w:H-h,"
            f"drawtext=fontfile='{font_path}':text='{clip_title}':"
            "x=45:y=(h-text_h)-10:fontsize=64:fontcolor=white:"
            "box=1:boxcolor=black@0.65:boxborderw=8"
        ),
        "-c:v",
        "libx264",
        "-b:v",
        "5M",  # Increase video bitrate for better quality
        "-c:a",
        "aac",
        "-b:a",
        "192k",  # Increase audio bitrate for better quality
        "-preset",
        "slow",  # Use a slower preset for better compression and quality
        "-movflags",
        "+faststart",
        output,
    ]

    subprocess.run(cmd)
