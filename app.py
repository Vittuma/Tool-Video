import os
import shutil
import uuid
import json
import asyncio
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List

from pipeline.extractor import extract_audio
from pipeline.transcriber import transcribe
from pipeline.tts import process_tts_segments, translate_text
from pipeline.merger import merge_all
import nest_asyncio

nest_asyncio.apply()

app = FastAPI()

# Setup folders
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
TASKS_DIR = "tasks_data" # Store json data for segments
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TASKS_DIR, exist_ok=True)

templates = Jinja2Templates(directory="templates")

# Task status storage
tasks_status = {}

class Segment(BaseModel):
    start: float
    end: float
    text: str
    translated_text: str = ""

class DubRequest(BaseModel):
    task_id: str
    segments: List[Segment]
    voice: str
    lang: str

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

async def run_step1_transcribe(task_id: str, input_path: str, target_lang: str):
    try:
        tasks_status[task_id] = {"status": "Đang tách âm thanh...", "step": 1}
        tmp_dir = os.path.join("tmp", task_id)
        os.makedirs(tmp_dir, exist_ok=True)
        
        # 1. Extract
        wav_path = extract_audio(input_path, tmp_dir)
        
        # 2. Transcribe
        tasks_status[task_id]["status"] = "Đang nhận diện giọng nói (Whisper)..."
        result = transcribe(wav_path)
        
        # 3. Initial Translation
        tasks_status[task_id]["status"] = "Đang dịch thô..."
        segments = []
        for seg in result['segments']:
            trans = await translate_text(seg['text'], target_lang)
            segments.append({
                "start": seg['start'],
                "end": seg['end'],
                "text": seg['text'],
                "translated_text": trans
            })
        
        # Save segments for editing
        with open(os.path.join(TASKS_DIR, f"{task_id}.json"), "w", encoding="utf-8") as f:
            json.dump({"segments": segments, "input_path": input_path}, f, ensure_ascii=False)
            
        tasks_status[task_id] = {"status": "Sẵn sàng để chỉnh sửa", "step": 2, "segments": segments}
        
    except Exception as e:
        tasks_status[task_id] = {"status": f"Lỗi: {str(e)}", "step": 0}

@app.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    lang: str = Form("vi")
):
    task_id = str(uuid.uuid4())
    input_filename = f"{task_id}_{video.filename}"
    input_path = os.path.join(UPLOAD_DIR, input_filename)
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)

    tasks_status[task_id] = {"status": "Đang khởi tạo...", "step": 1}
    background_tasks.add_task(run_step1_transcribe, task_id, input_path, lang)

    return {"task_id": task_id}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    return tasks_status.get(task_id, {"status": "Không tìm thấy task", "step": 0})

@app.post("/dub")
async def start_dubbing(req: DubRequest, background_tasks: BackgroundTasks):
    task_id = req.task_id
    # Update saved segments with user edits
    task_file = os.path.join(TASKS_DIR, f"{task_id}.json")
    if not os.path.exists(task_file):
        raise HTTPException(status_code=404, detail="Task data not found")
    
    with open(task_file, "r") as f:
        data = json.load(f)
    
    data['segments'] = [s.dict() for s in req.segments]
    with open(task_file, "w") as f:
        json.dump(data, f)
        
    tasks_status[task_id] = {"status": "Đang tiến hành Dubbing (TTS & Merge)...", "step": 3}
    background_tasks.add_task(run_step2_dub, task_id, req.voice, req.lang)
    
    return {"status": "Started"}

async def run_step2_dub(task_id: str, voice: str, lang: str):
    try:
        task_file = os.path.join(TASKS_DIR, f"{task_id}.json")
        with open(task_file, "r") as f:
            data = json.load(f)
            
        tmp_dir = os.path.join("tmp", task_id)
        input_path = data['input_path']
        output_path = os.path.join(OUTPUT_DIR, f"dubbed_{task_id}.mp4")
        
        # Prepare segments for TTS (convert back to format expected by pipeline)
        # pipeline/tts.py needs 'text' to be the one to speak
        tts_segments = []
        for s in data['segments']:
            tts_segments.append({
                "start": s['start'],
                "end": s['end'],
                "text": s['translated_text'] # Speak the translated text
            })
            
        # 1. TTS
        processed = await process_tts_segments(tts_segments, tmp_dir, lang, voice)
        
        # 2. Merge
        merge_all(input_path, processed, output_path)
        
        tasks_status[task_id] = {
            "status": "Hoàn thành", 
            "step": 4, 
            "download_url": f"/download/{task_id}"
        }
        
        # Optional: cleanup tmp
        # shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception as e:
        tasks_status[task_id] = {"status": f"Lỗi Dubbing: {str(e)}", "step": 0}

@app.get("/download/{task_id}")
async def download_video(task_id: str):
    output_path = os.path.join(OUTPUT_DIR, f"dubbed_{task_id}.mp4")
    if os.path.exists(output_path):
        return FileResponse(output_path, filename="dubbed_video.mp4")
    return {"error": "File not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
