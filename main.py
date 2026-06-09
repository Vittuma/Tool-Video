import os
import asyncio
import whisper
import numpy as np
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, ImageClip, ColorClip
from googletrans import Translator
import edge_tts
from tqdm import tqdm
from PIL import Image, ImageDraw, ImageFont

class VideoTranslator:
    def __init__(self, model_size="base"):
        print(f"Loading Whisper model ({model_size})...")
        self.model = whisper.load_model(model_size)
        self.translator = Translator()

    async def translate_text(self, text, target_lang="vi"):
        if not text.strip():
            return ""
        try:
            result = self.translator.translate(text, dest=target_lang)
            return result.text
        except Exception as e:
            print(f"Translation error: {e}")
            return text

    async def text_to_speech(self, text, output_path, voice="vi-VN-HoaiMyNeural", rate="+0%"):
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(output_path)

    def create_subtitle_image(self, text, width, height, font_size=24, color="white", bg_color=(0, 0, 0, 150)):
        # Simple PIL based subtitle generator to avoid ImageMagick dependency
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Load a font - default to a common one or system default
        try:
            # Try some common fonts on macOS
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Get text bounding box to center it
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = height - text_height - 20 # 20px from bottom
        
        # Draw background box to cover old subs
        draw.rectangle([x - 10, y - 5, x + text_width + 10, y + text_height + 5], fill=bg_color)
        draw.text((x, y), text, font=font, fill=color)
        
        return np.array(img)

    def process_video(self, input_path, output_path, target_lang="vi", voice="vi-VN-HoaiMyNeural"):
        # 1. Load Video
        video = VideoFileClip(input_path)
        w, h = video.size
        
        # 2. Extract Audio
        audio_path = "temp_audio.wav"
        video.audio.write_audiofile(audio_path, logger=None)

        # 3. Transcribe
        print("Transcribing video...")
        result = self.model.transcribe(audio_path, verbose=False)
        segments = result['segments']

        # 4. Translate and Generate TTS
        print(f"Translating and generating TTS/Subs (Target: {target_lang})...")
        
        async def process_all():
            audio_clips = []
            subtitle_clips = []
            
            for i, segment in enumerate(tqdm(segments)):
                original_text = segment['text']
                start = segment['start']
                end = segment['end']
                duration = end - start
                
                if not original_text.strip():
                    continue

                translated_text = await self.translate_text(original_text, target_lang)
                
                # Generate TTS
                seg_audio_path = f"seg_{i}.mp3"
                await self.text_to_speech(translated_text, seg_audio_path, voice)
                
                seg_audio = AudioFileClip(seg_audio_path)
                
                # If TTS is longer than original, speed it up
                if seg_audio.duration > duration and duration > 0:
                    speed_increase = int((seg_audio.duration / duration - 1) * 100)
                    speed_increase = min(speed_increase, 100)
                    rate = f"+{speed_increase}%"
                    await self.text_to_speech(translated_text, seg_audio_path, voice, rate=rate)
                    seg_audio = AudioFileClip(seg_audio_path)
                
                seg_audio = seg_audio.with_start(start)
                audio_clips.append(seg_audio)
                
                # Subtitle
                sub_img = self.create_subtitle_image(translated_text, w, h)
                sub_clip = ImageClip(sub_img).with_start(start).with_duration(duration)
                subtitle_clips.append(sub_clip)
                
            return audio_clips, subtitle_clips

        audio_clips, subtitle_clips = asyncio.run(process_all())

        # 5. Combine
        print("Mixing everything...")
        # Black bar at the bottom to better cover old subtitles
        # We can also just rely on the background box in create_subtitle_image
        
        final_audio = CompositeAudioClip(audio_clips)
        final_video = CompositeVideoClip([video] + subtitle_clips)
        final_video = final_video.with_audio(final_audio)
        
        # 6. Output
        print(f"Writing output to {output_path}...")
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", temp_audiofile="temp-audio.m4a", remove_temp=True)
        
        # Cleanup
        video.close()
        final_video.close()
        for i in range(len(segments)):
            if os.path.exists(f"seg_{i}.mp3"):
                os.remove(f"seg_{i}.mp3")
        if os.path.exists("temp_audio.wav"):
            os.remove("temp_audio.wav")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Video Translator")
    parser.add_argument("--input", required=True, help="Input video file")
    parser.add_argument("--output", default="output.mp4", help="Output video file")
    parser.add_argument("--lang", default="vi", help="Target language code")
    parser.add_argument("--voice", default="vi-VN-HoaiMyNeural", help="Edge TTS voice name")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found.")
    else:
        translator = VideoTranslator()
        translator.process_video(args.input, args.output, args.lang, args.voice)
