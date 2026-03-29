import sys
import subprocess
try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "youtube-transcript-api"])
    from youtube_transcript_api import YouTubeTranscriptApi

def get_vid(vid_id, out_name):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(vid_id)
        text = " ".join([t['text'] for t in transcript])
        with open(out_name, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"{vid_id} success")
    except Exception as e:
        print(f"{vid_id} failed: {e}")

get_vid('qKU-e0x2EmE', 'vid1.txt')
get_vid('4Cb_l2LJAW8', 'vid2.txt')
