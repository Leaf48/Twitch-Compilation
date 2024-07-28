import subprocess


def merge_video_with_comment(video_path: str, comment_path: str, output: str):
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
        "[1]crop=in_w:100:0:in_h-100,format=rgba,colorchannelmixer=aa=0.5[ov];[0][ov]overlay=W-w:H-h",
        "-c:v",
        "libx264",
        "-b:v",
        "1M",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-preset",
        "medium",
        "-movflags",
        "+faststart",
        output,
    ]
    subprocess.run(cmd)
