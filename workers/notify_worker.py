from fastapi.responses import StreamingResponse
from fastapi import APIRouter
import time


# Global dictionary to hold worker notifications
worker_notifications = {}

# Global dictionary to hold user notifications
user_notifications = {}

sse_router = APIRouter()


# Event Stream Function
def event_stream(worker_id: int):
    while True:
        # Check if there are any notifications for the worker
        if worker_notifications.get(worker_id):
            while worker_notifications[worker_id]:
                notification = worker_notifications[worker_id].pop(0)
                yield f"data: {notification}\n\n"
        time.sleep(5)  # Heartbeat to keep connection alive


# SSE Endpoint for Worker to listen to real-time notifications
@sse_router.get("/sse/worker/{worker_id}", tags=["SSE"])
async def worker_sse(worker_id: int):
    # Register worker if not already in the notifications dictionary
    if worker_id not in worker_notifications:
        worker_notifications[worker_id] = []
        
    # Start streaming notifications
    return StreamingResponse(event_stream(worker_id), media_type="text/event-stream")

