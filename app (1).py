import os
os.environ['IMAGEMAGICK_BINARY'] = '/usr/bin/convert'
import moviepy.editor as mp
from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
from gtts import gTTS
# from transformers import pipeline, AutoTokenizer
import tempfile
import captioning

# Debugging: print the ImageMagick binary path
print("Using ImageMagick binary at:", os.environ.get('IMAGEMAGICK_BINARY'))
# image_to_text = pipeline("image-to-text", model="nlpconnect/vit-gpt2-image-captioning")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['PROCESSED_FOLDER'] = 'static/processed'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB max size
app.config['MIDDLE_FRAME'] = 'static/processed'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

def generate_caption(video_path):
    # Load video
    video = mp.VideoFileClip(video_path)

    # Extract frames from video
    middle_frame_index = int(video.duration / 2)

    # Get the middle frame
    middle_frame = video.get_frame(middle_frame_index)

    middle_frame_path = os.path.join(app.config['MIDDLE_FRAME'], "middle_frame.jpg")
    mp.ImageClip(middle_frame).save_frame(middle_frame_path)
    caption = captioning.predict_step(middle_frame_path)
    return caption[0]

def add_caption_and_tts(video_path, caption):
    video = mp.VideoFileClip(video_path)
    tts = gTTS(text=caption, lang='en')
    audio_path = os.path.join(app.config['PROCESSED_FOLDER'], 'audio.mp3')
    tts.save(audio_path)
    audio = mp.AudioFileClip(audio_path)
    video = video.set_audio(audio)
    txt_clip = mp.TextClip(caption, fontsize=24, color='white', size=video.size)
    txt_clip = txt_clip.set_pos('bottom').set_duration(video.duration)
    video = mp.CompositeVideoClip([video, txt_clip])
    processed_video_path = os.path.join(app.config['PROCESSED_FOLDER'], 'processed_video.mp4')
    video.write_videofile(processed_video_path)
    return processed_video_path

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'video' not in request.files:
            return 'No video part'
        file = request.files['video']
        if file.filename == '':
            return 'No selected video'
        if file:
            filename = secure_filename(file.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(video_path)
            caption = generate_caption(video_path)
            processed_video_path = add_caption_and_tts(video_path, caption)
            processed_video_filename = os.path.basename(processed_video_path)
            return render_template('display_video.html', video_file=processed_video_filename, caption=caption)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
