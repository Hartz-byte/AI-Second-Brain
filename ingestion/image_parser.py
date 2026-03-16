import base64
from openai import OpenAI
from backend.config import GROQ_API_KEY, API_BASE

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=API_BASE
)

def analyze_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """
    Takes image bytes, converts to base64, and sends to Groq Vision model
    for OCR and detailed semantic description.
    """
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    prompt = "Transcribe any text found in this image exactly as written. Then, provide a detailed description of the visual content, context, and any data presented."
    
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Vision API Error: {str(e)}")
