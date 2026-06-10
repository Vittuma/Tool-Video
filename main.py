import os
import shutil
import asyncio
from pipeline.extractor import extract_audio
from pipeline.transcriber import transcribe
from pipeline.tts import process_tts_segments
from pipeline.merger import merge_all

class VideoDubbingPipeline:
    def __init__(self, tmp_dir="./tmp_processing"):
        self.tmp_dir = tmp_dir
        os.makedirs(self.tmp_dir, exist_ok=True)

    async def run(self, input_video: str, output_video: str, target_lang: str = "vi", voice: str = "vi-VN-HoaiMyNeural"):
        try:
            # 1. Tách audio
            wav_path = extract_audio(input_video, self.tmp_dir)

            # 2. Transcribe
            result = transcribe(wav_path)
            
            # 3. Dịch và TTS
            processed_segments = await process_tts_segments(result['segments'], self.tmp_dir, target_lang, voice)

            # 4. Ghép video
            merge_all(input_video, processed_segments, output_video)

            return output_video
        finally:
            # Clean up segments but keep output (handled by app.py)
            pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="output.mp4")
    parser.add_argument("--lang", default="vi")
    parser.add_argument("--voice", default="vi-VN-HoaiMyNeural")
    args = parser.parse_args()
    
    pipeline = VideoDubbingPipeline()
    asyncio.run(pipeline.run(args.input, args.output, args.lang, args.voice))
