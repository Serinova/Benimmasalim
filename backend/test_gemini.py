import asyncio
from app.services.image_processing import image_processing_service
from app.config import settings

async def main():
    print(f"Key preview: {settings.gemini_api_key[:10]}...")
    # create a dummy image
    from PIL import Image
    import io
    img = Image.new('RGB', (100, 100), color='red')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    img_bytes = buf.getvalue()
    
    try:
        print("calling convert_to_line_art_ai...")
        res = await image_processing_service.convert_to_line_art_ai(img_bytes)
        print("Success! Got bytes:", len(res))
    except Exception as e:
        print("Failed:", repr(e))

if __name__ == "__main__":
    asyncio.run(main())
