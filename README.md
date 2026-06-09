# Video Translator Tool

Công cụ này giúp bạn dịch cả giọng nói (voice) và chữ trên video (subtitles) sang ngôn ngữ mong muốn.

## Tính năng
- **Dịch giọng nói (Dubbing)**: Sử dụng AI để nghe giọng gốc, dịch sang tiếng Việt (hoặc ngôn ngữ khác) và lồng tiếng mới bằng giọng đọc tự nhiên.
- **Dịch phụ đề (Subbing)**: Tự động tạo phụ đề mới và chèn đè lên vị trí phụ đề cũ trên video.
- **Khớp thời gian**: Tự động tăng tốc độ giọng đọc nếu câu dịch dài hơn câu gốc để đảm bảo khớp với video.
- **Không cần ImageMagick**: Sử dụng thư viện Pillow để tạo sub, giúp cài đặt dễ dàng hơn.

## Cài đặt

1. **Yêu cầu**: Python 3.8+
2. **Cài đặt thư viện**:
   ```bash
   pip install moviepy openai-whisper googletrans==4.0.0-rc1 edge-tts pillow tqdm numpy
   ```
3. **FFmpeg**: Đảm bảo hệ thống đã cài đặt FFmpeg (thường có sẵn trên Linux/macOS, hoặc tải về trên Windows).

## Cách sử dụng

Chạy lệnh sau trong terminal:

```bash
python main.py --input path/to/video.mp4 --output video_da_dich.mp4 --lang vi --voice vi-VN-HoaiMyNeural
```

### Các tham số:
- `--input`: Đường dẫn tới file video gốc.
- `--output`: Tên file video đầu ra (mặc định: `output.mp4`).
- `--lang`: Mã ngôn ngữ muốn dịch sang (ví dụ: `vi` cho tiếng Việt, `en` cho tiếng Anh).
- `--voice`: Tên giọng đọc của Edge-TTS. 
  - Một số giọng tiếng Việt hay: `vi-VN-HoaiMyNeural`, `vi-VN-NamMinhNeural`.

## Lưu ý
- Lần đầu chạy sẽ mất thời gian tải model Whisper (khoảng 150MB cho bản `base`).
- Công cụ sử dụng Google Translate (miễn phí) nên có thể gặp giới hạn nếu dịch quá nhiều cùng lúc.
- Việc che sub cũ được thực hiện bằng một dải màu đen mờ phía sau sub mới.
