from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)

        text = " ".join([t["text"] for t in transcript])

        return text

    except Exception as e:
        print("Transcript error:", e)
        return None
