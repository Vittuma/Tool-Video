import whisper
import os

def transcribe(audio_path: str, model_size="tiny") -> dict:
    """
    Transcribe file WAV → text kèm timestamps sử dụng OpenAI Whisper (Local).
    Sử dụng model 'tiny' để tối ưu RAM cho Railway.
    """
    print(f"[transcriber] Đang load model Whisper ({model_size})...")
    model = whisper.load_model(model_size)
    
    print("[transcriber] Đang thực hiện transcription...")
    result = model.transcribe(audio_path, verbose=False)
    
    segments = [
        {
            "start": seg['start'],
            "end": seg['end'],
            "text": seg['text'].strip()
        }
        for seg in result['segments']
    ]

    print(f"[transcriber] Transcribe xong — {len(segments)} segments")
    return {
        "text": result['text'],
        "segments": segments
    }
