import os
from dotenv import load_dotenv

# Load environment variables (.env)
load_dotenv()

from fastapi import APIRouter, UploadFile, File, HTTPException
from openai import OpenAI

router = APIRouter(prefix="/api/voice", tags=["voice"])

# Lazy-initialize OpenAI client for Whisper transcription
_openai_client = None

# Common Whisper hallucinations triggered by ambient background noise or silence
NOISE_HALLUCINATIONS = {
    "thank you",
    "thank you.",
    "thanks for watching",
    "thanks for watching.",
    "subtitles by",
    "you",
    "you.",
    "bye",
    "bye.",
    "mbc",
    "please subscribe",
    "like and subscribe",
}


def _get_openai_client() -> OpenAI:
    """Get or create the OpenAI client for Whisper transcription."""
    global _openai_client
    if _openai_client is None:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ [Whisper] OPENAI_API_KEY is missing from environment!")
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY not configured on server",
            )
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Receive an audio file (.wav or .m4a) from the mobile app and transcribe it
    using OpenAI Whisper with clinical context grounding and noise filtering.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")

    client = _get_openai_client()

    try:
        audio_bytes = await file.read()
        print(f"📥 [Whisper] Received audio file: {file.filename} ({len(audio_bytes)} bytes)")

        if len(audio_bytes) < 300:
            print("🔇 [Whisper] Audio file is too short/empty (<300 bytes)")
            return {"text": ""}

        # Determine file extension and MIME type
        filename = file.filename or "recording.wav"
        if not ("." in filename):
            filename += ".wav"
        
        content_type = file.content_type or ("audio/wav" if filename.endswith(".wav") else "audio/m4a")

        # Pass in-memory audio tuple directly to OpenAI Whisper API
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, audio_bytes, content_type),
            language="en",
            temperature=0.0,
        )

        transcript_text = transcription.text.strip()
        print(f"🎙️ [Whisper Raw Output]: \"{transcript_text}\"")

        # Filter out background noise hallucinations
        clean_lower = transcript_text.lower().strip()
        if clean_lower in NOISE_HALLUCINATIONS or len(transcript_text) < 2:
            print(f"🔇 [Whisper] Filtered background noise artifact: \"{transcript_text}\"")
            return {"text": ""}

        print(f"✅ [Whisper Final Result]: \"{transcript_text}\"")
        return {"text": transcript_text}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [Whisper Exception]: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}",
        )
