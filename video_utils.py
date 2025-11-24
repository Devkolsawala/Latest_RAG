import cv2
import base64
import os
import requests
import json

def extract_frames(video_path, max_frames=8):
    """
    Extracts evenly distributed frames from a video file.
    """
    if not os.path.exists(video_path):
        return []

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if total_frames <= 0:
        return []

    frames = []
    step = max(1, total_frames // max_frames)

    for i in range(0, total_frames, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize frame to reduce payload size (max dimension 768px)
        height, width = frame_rgb.shape[:2]
        max_dim = 768
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame_rgb = cv2.resize(frame_rgb, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Encode to base64
        _, buffer = cv2.imencode('.jpg', frame_rgb, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        frames.append(f"data:image/jpeg;base64,{frame_base64}")
        
        if len(frames) >= max_frames:
            break
            
    cap.release()
    return frames

def get_video_summary(frames, api_key):
    """
    Sends frames to OpenRouter using nvidia/nemotron-nano-12b-v2-vl:free for summarization.
    """
    if not frames:
        return "No frames could be extracted from the video."

    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Construct the message content with text and images
    # Construct the message content with text and images
    content = [{"type": "text", "text": "These are sequential frames from a video. Please provide a detailed, cohesive summary of the event taking place. Describe the action as a continuous narrative. IMPORTANT: Do NOT mention specific frame numbers (e.g., 'Frame 1', 'In the first frame'). Just describe what happens in the video."}]
    
    for frame in frames:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": frame
            }
        })

    data = {
        "model": "nvidia/nemotron-nano-12b-v2-vl:free",
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ],
        "temperature": 0.5,
        "max_tokens": 1024
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            return f"Error: {response.status_code} - {response.text}"
        
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"Error generating summary: {str(e)}"
