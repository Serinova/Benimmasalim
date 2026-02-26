import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import jwt
from datetime import datetime, timedelta, timezone
import httpx

async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres:BnmMsl2026ProdDB!@localhost:5433/benimmasalim')
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT id FROM users WHERE role = 'admin' LIMIT 1"))
        row = res.fetchone()
        if not row:
            print('No admin users found!')
            return
        admin_id = str(row[0])
        print(f'Found admin ID: {admin_id}')
        
    await engine.dispose()
    
    secret = '88801a36f02496279b4443f8f14653d4f68ff102eff52026d2d8f5c2a93e385b'
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=60)
    to_encode = {
        'sub': admin_id,
        'exp': expire,
        'iat': now,
        'iss': 'benimmasalim',
        'aud': 'benimmasalim-api',
        'type': 'access',
        'role': 'admin'
    }
    
    access_token = jwt.encode(to_encode, secret, algorithm='HS256')
    
    trial_ids = [
        '0f63841a-0cd9-4a55-9548-fc8a99adfb31',
        '7136ee83-4c2c-4c0d-ab3a-5641d8f68c63',
        'eefa582c-ef96-4b43-b4b4-3c82f95cebb9'
    ]
    
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    base_url = 'https://benimmasalim-backend-554846094227.europe-west1.run.app/api/v1'
    
    async with httpx.AsyncClient(timeout=30) as client:
        for tid in trial_ids:
            url = f'{base_url}/admin/orders/previews/{tid}/generate-coloring-book'
            print(f'Triggering {tid}...')
            r = await client.post(url, headers=headers)
            print(r.status_code, r.text)

asyncio.run(main())
