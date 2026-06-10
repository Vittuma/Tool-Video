import ffmpeg
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def create_subtitle_image(text, width, height, font_size=24):
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = (width - tw) // 2, height - th - 30
    
    draw.rectangle([x - 10, y - 5, x + tw + 10, y + th + 5], fill=(0, 0, 0, 160))
    draw.text((x, y), text, font=font, fill="white")
    return img

def merge_all(video_path, segments, output_path):
    """
    Sử dụng ffmpeg-python để ghép audio và overlay subtitle.
    """
    # 1. Get Video info
    probe = ffmpeg.probe(video_path)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    width = int(video_stream['width'])
    height = int(video_stream['height'])

    # 2. Build Audio Stream
    # We use 'adelay' and 'amix' for precise positioning
    audio_inputs = []
    for seg in segments:
        delay = int(seg['start'] * 1000)
        a = ffmpeg.input(seg['audio_path']).filter('adelay', f"{delay}|{delay}")
        audio_inputs.append(a)
    
    mixed_audio = ffmpeg.filter(audio_inputs, 'amix', inputs=len(audio_inputs), dropout_transition=0)

    # 3. (Optional) Build Subtitles via complex filter or SRT
    # For this modular version, we keep it simple: Replace audio first.
    # Subtitles in ffmpeg are easier via .srt file.
    
    video = ffmpeg.input(video_path)
    
    (
        ffmpeg
        .output(video.video, mixed_audio, output_path, vcodec='copy', acodec='aac')
        .overwrite_output()
        .run(quiet=True)
    )
    print(f"[merger] Hoàn tất → {output_path}")
