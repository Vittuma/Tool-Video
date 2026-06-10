import ffmpeg
import os

def extract_audio(input_video: str, output_dir: str) -> str:
    """
    Tách audio từ video MP4, lưu ra WAV 16kHz mono.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_wav = os.path.join(output_dir, "audio.wav")

    try:
        (
            ffmpeg
            .input(input_video)
            .output(output_wav, ar=16000, ac=1, format='wav')
            .overwrite_output()
            .run(quiet=True)
        )
        print(f"[extractor] Đã tách audio → {output_wav}")
        return output_wav
    except ffmpeg.Error as e:
        print(f"Extractor Error: {e.stderr.decode()}")
        raise e
