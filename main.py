import subprocess
import json
import time
from flask import Flask, Response, send_from_directory, render_template
import os
from threading import Thread

app = Flask(__name__)

# decorator to measure time taken by a function
def timeit(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        print(f"Time taken: {end - start}")
    return wrapper

def get_video_info(input_file):
    # Command to get video file information in JSON format
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_streams',
        '-select_streams', 'v',
        input_file
    ]
    result = subprocess.run(cmd, capture_output=True)
    return json.loads(result.stdout)

def calculate_scale_params(width, height, max_width=1920, max_height=1080):
    # Maintain aspect ratio while scaling down to max_width x max_height
    aspect_ratio = width / height
    if width > max_width or height > max_height:
        if width / max_width < height / max_height:
            width = int(max_height * aspect_ratio)
            height = max_height
        else:
            height = int(max_width / aspect_ratio)
            width = max_width
    return width, height

def generate_output_filename(input_file):
    base, ext = os.path.splitext(input_file)
    return f"[transcoded]{base}{ext}"

def transcode_video(input_file, output_file):
    # Get information about the source video
    video_info = get_video_info(input_file)
    width = video_info['streams'][0]['width']
    height = video_info['streams'][0]['height']

    # Calculate the scaling parameters
    scaled_width, scaled_height = calculate_scale_params(width, height)

    command = [
        'ffmpeg',
        '-hwaccel', 'qsv',
        '-c:v', 'hevc_qsv',  # Decoder
        '-i', input_file,
        '-vf', f'scale_qsv=w={scaled_width}:h={scaled_height}',  # Use scale_qsv for scaling with QSV
        '-c:v', 'hevc_qsv',  # Encoder
        '-b:v', '10M',
        '-c:a', 'copy',
        '-c:s', 'copy',
        output_file
    ]

    subprocess.run(command)

def transcode_video_to_hls(input_file, output_dir):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # FFmpeg command to segment the video
    command = [
        'ffmpeg',
        '-i', input_file,
        '-codec:', 'copy',  # Copy video and audio codecs
        '-start_number', '0',  # Start segmenting from 0
        '-hls_time', '10',  # Duration of each segment in seconds
        '-hls_playlist_type', 'vod',  # Type of playlist
        '-f', 'hls',  # HLS format
        os.path.join(output_dir, 'output.m3u8')  # Output playlist
    ]
    
    subprocess.run(command)

@app.route('/stream_video')
def stream_video():
    input_file = 'mand.mkv'
    output_dir = 'hls_output'  # Directory to store HLS files
    transcoding_thread = Thread(target=transcode_video_to_hls, args=(input_file, output_dir))
    transcoding_thread.start()

    # Check for the existence of the first segment
    first_segment = os.path.join(output_dir, 'segment0.ts')
    while not os.path.exists(first_segment):
        time.sleep(1)  # Check every second
        
    return send_from_directory(output_dir, 'output.m3u8', as_attachment=True)

@app.route('/hls_output/<filename>')
def serve_hls_segment(filename):
    return send_from_directory('hls_output', filename)


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
