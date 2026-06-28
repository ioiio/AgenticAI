import os
import asyncio
from groq import AsyncGroq
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

async def test():
    client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
    res = await client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": "Ping"}]
    )
    print("API Response:", res.choices[0].message.content)

asyncio.run(test())