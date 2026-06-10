import os
import edge_tts
import asyncio
from googletrans import Translator

async def translate_text(text: str, target_lang="vi"):
    if not text.strip(): return ""
    translator = Translator()
    try:
        # Note: In a production loop, we might want to reuse the Translator object
        result = translator.translate(text, dest=target_lang)
        return result.text
    except Exception as e:
        print(f"Translation error: {e}")
        return text

async def text_to_speech_edge(text: str, output_path: str, voice: str = "vi-VN-HoaiMyNeural", rate="+0%"):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)

async def process_tts_segments(segments: list, output_dir: str, target_lang: str, voice: str):
    """
    Dịch và chuyển đổi từng segment sang audio.
    """
    processed_segments = []
    for i, seg in enumerate(segments):
        translated = await translate_text(seg['text'], target_lang)
        seg_path = os.path.join(output_dir, f"seg_{i:03d}.mp3")
        
        # Calculate duration to adjust speed if necessary
        duration = seg['end'] - seg['start']
        
        # Initial TTS
        await text_to_speech_edge(translated, seg_path, voice)
        
        # For simplicity in this modular version, we just save the path
        # Advanced: Check duration and re-generate with speed adjustment
        
        processed_segments.append({
            "start": seg['start'],
            "end": seg['end'],
            "text": translated,
            "audio_path": seg_path
        })
    return processed_segments
