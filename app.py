import os
import shutil
import uuid
import asyncio
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from main import VideoTranslator

app = FastAPI()

# Setup folders
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

templates = Jinja2Templates(directory="templates")

# Store status of tasks
tasks = {}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

async def run_translation(task_id: str, input_path: str, output_path: str, lang: str, voice: str):
    try:
        tasks[task_id] = "Đang xử lý (Transcription & Translation)..."
        # Use a smaller model for web demo if needed, here we use 'base'
        translator = VideoTranslator(model_size="base")
        await translator.process_video(input_path, output_path, lang, voice)
        tasks[task_id] = "Hoàn thành"
    except Exception as e:
        tasks[task_id] = f"Lỗi: {str(e)}"
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

@app.post("/translate")
async def translate_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    lang: str = Form("vi"),
    voice: str = Form("vi-VN-HoaiMyNeural")
):
    task_id = str(uuid.uuid4())
    input_filename = f"{task_id}_{video.filename}"
    input_path = os.path.join(UPLOAD_DIR, input_filename)
    output_filename = f"translated_{task_id}.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)

    tasks[task_id] = "Đã nhận file, đang chờ xử lý..."
    background_tasks.add_task(run_translation, task_id, input_path, output_path, lang, voice)

    return {"task_id": task_id, "status": "Started"}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    status = tasks.get(task_id, "Không tìm thấy task")
    download_url = f"/download/{task_id}" if status == "Hoàn thành" else None
    return {"status": status, "download_url": download_url}

@app.get("/download/{task_id}")
async def download_video(task_id: str):
    output_filename = f"translated_{task_id}.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    if os.path.exists(output_path):
        return FileResponse(output_path, media_type="video/mp4", filename="translated_video.mp4")
    return {"error": "File không tồn tại hoặc chưa xử lý xong"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
