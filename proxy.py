from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import httpx
import uuid
from collections import deque
from cachetools import TTLCache

app = FastAPI(title="Classification Proxy", description="Optimized Proxy with Batching and LRU Cache")

CLASSIFICATION_SERVER_URL = "http://localhost:8001/classify"
MAX_BATCH_SIZE = 5
BATCH_TIMEOUT = 0.05  # 50ms

# LRU cache with max size 50 and TTL 300s
cache = TTLCache(maxsize=50, ttl=300)

class ProxyRequest(BaseModel):
    sequence: str

class ProxyResponse(BaseModel):
    result: str

# Shared structures
request_queue = deque()
response_futures = {}

@app.on_event("startup")
async def start_batch_worker():
    asyncio.create_task(batch_worker())

@app.post("/proxy_classify")
async def proxy_classify(req: ProxyRequest) -> ProxyResponse:
    sequence = req.sequence

    # Check LRU + TTL cache
    if sequence in cache:
        return ProxyResponse(result=cache[sequence])

    request_id = str(uuid.uuid4())
    fut = asyncio.get_event_loop().create_future()

    response_futures[request_id] = fut
    request_queue.append((request_id, sequence))

    result = await fut
    return ProxyResponse(result=result)

async def batch_worker():
    while True:
        await asyncio.sleep(BATCH_TIMEOUT)

        if not request_queue:
            continue

        batch = []
        while len(batch) < MAX_BATCH_SIZE and request_queue:
            batch.append(request_queue.popleft())

        request_ids, sequences = zip(*batch)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(CLASSIFICATION_SERVER_URL, json={"sequences": list(sequences)})
                if resp.status_code == 200:
                    results = resp.json()["results"]

                    for rid, seq, result in zip(request_ids, sequences, results):
                        cache[seq] = result  # Store in LRU TTL cache
                        if rid in response_futures:
                            response_futures[rid].set_result(result)
                            del response_futures[rid]
                else:
                    for rid in request_ids:
                        if rid in response_futures:
                            response_futures[rid].set_exception(Exception("Classification failed"))
                            del response_futures[rid]
        except Exception as e:
            for rid in request_ids:
                if rid in response_futures:
                    response_futures[rid].set_exception(e)
                    del response_futures[rid]
