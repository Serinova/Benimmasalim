import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.services.ai.face_analyzer_service import get_face_analyzer


async def main():
    analyzer = get_face_analyzer()
    image_path = r"C:\Users\yusuf\OneDrive\Belgeler\BenimMasalim\WhatsApp Image 2026-02-11 at 18.33.33 (1).jpeg"
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    base64_data, mime_type = await analyzer._load_image_as_base64(image_bytes)
    
    url = f"{analyzer.base_url}/models/{analyzer.model}:generateContent?key={analyzer.api_key}"
    
    import httpx
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"inlineData": {"mimeType": mime_type, "data": base64_data}},
                    {"text": "Analyze this face in detail."},
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
        },
    }
    
    print(f"Calling {analyzer.model}...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)
        print("Status Code:", response.status_code)
        import json
        print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    asyncio.run(main())
