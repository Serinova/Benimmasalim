"""Direct test of Fal.ai API - bypass all system logic."""
import asyncio
import sys
sys.path.insert(0, ".")

import httpx
from app.config import settings

FAL_QUEUE_BASE = "https://queue.fal.run"

async def test_direct():
    """Test Fal.ai directly with a simple prompt."""
    
    api_key = settings.fal_api_key
    if not api_key:
        print("ERROR: FAL_API_KEY not set!")
        return
    
    # Simple, clear prompt
    test_prompt = """Istanbul Turkey cityscape with the iconic Hagia Sophia dome, Blue Mosque with six minarets, Galata Tower, and Bosphorus strait with ferries. Golden sunset light. A young boy standing small in the foreground, looking at the historic landmarks. Wide shot, detailed background. Children's book illustration style."""
    
    negative_prompt = """asian architecture, chinese building, japanese temple, pagoda, thai temple, palm trees, tropical forest, jungle, thatched roof hut"""
    
    print("="*60)
    print("DIRECT FAL.AI TEST")
    print("="*60)
    print(f"\nPROMPT:\n{test_prompt}")
    print(f"\nNEGATIVE:\n{negative_prompt}")
    print("="*60)
    
    # Payload for Flux DEV (no face reference)
    payload = {
        "prompt": test_prompt,
        "negative_prompt": negative_prompt,
        "image_size": {
            "width": 1024,
            "height": 768,
        },
        "num_inference_steps": 28,
        "guidance_scale": 3.5,
    }
    
    print(f"\nSending to: fal-ai/flux/dev")
    print(f"Payload: {payload}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Submit to queue
            response = await client.post(
                f"{FAL_QUEUE_BASE}/fal-ai/flux/dev",
                headers={
                    "Authorization": f"Key {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            
            print(f"\nResponse status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error: {response.text}")
                return
            
            result = response.json()
            print(f"\nResult: {result}")
            
            # Get image URL
            if "images" in result:
                image_url = result["images"][0]["url"]
                print(f"\n✅ SUCCESS! Image URL:\n{image_url}")
            elif "request_id" in result:
                print(f"\nQueued. Request ID: {result['request_id']}")
                print("Waiting for result...")
                
                # Poll for result
                request_id = result["request_id"]
                for i in range(30):
                    await asyncio.sleep(3)
                    
                    status_response = await client.get(
                        f"{FAL_QUEUE_BASE}/fal-ai/flux/dev/requests/{request_id}/status",
                        headers={"Authorization": f"Key {api_key}"},
                    )
                    status = status_response.json()
                    print(f"  Status check {i+1}: {status.get('status', 'unknown')}")
                    
                    if status.get("status") == "COMPLETED":
                        # Get result
                        result_response = await client.get(
                            f"{FAL_QUEUE_BASE}/fal-ai/flux/dev/requests/{request_id}",
                            headers={"Authorization": f"Key {api_key}"},
                        )
                        final_result = result_response.json()
                        
                        if "images" in final_result:
                            image_url = final_result["images"][0]["url"]
                            print(f"\n✅ SUCCESS! Image URL:\n{image_url}")
                        else:
                            print(f"\nResult: {final_result}")
                        break
                    elif status.get("status") == "FAILED":
                        print(f"\n❌ FAILED: {status}")
                        break
            else:
                print(f"\nUnexpected response: {result}")
                
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(test_direct())
