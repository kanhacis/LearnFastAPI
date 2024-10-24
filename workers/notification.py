from fastapi.responses import StreamingResponse
from fastapi import APIRouter
import time


# Global dictionary to hold worker notifications
worker_notifications = {}

# Global dictionary to hold user notifications
user_notifications = {}

sse_router = APIRouter()

## Event Stream Function for worker notification
def event_stream_worker(worker_id: int):
    while True:
        # Check if there are any notifications for the worker
        if worker_notifications.get(worker_id):
            while worker_notifications[worker_id]:
                notification = worker_notifications[worker_id].pop(0)
                yield f"data: {notification}\n\n"
        time.sleep(5)  # Heartbeat to keep connection alive


## SSE Endpoint for Worker to listen to real-time notifications
@sse_router.get("/sse/worker/{worker_id}", tags=["SSE"])
async def worker_sse(worker_id: int):
    # Register worker if not already in the worker notifications dictionary
    if worker_id not in worker_notifications:
        worker_notifications[worker_id] = []
        
    # Start streaming worker notifications
    return StreamingResponse(event_stream_worker(worker_id), media_type="text/event-stream")


## Event Stream Function for user notification 
def event_stream_user(request_id: int):
    while True:
        # Check if there are any notifications for the user
        if user_notifications.get(request_id):
            while user_notifications[request_id]:
                notification = user_notifications[request_id].pop(0)
                yield f"data: {notification}\n\n"

## SSE Endpoint for User to listen to real-time notifications 
@sse_router.get("/sse/user/{request_id}", tags=["SSE"])
async def user_sse(request_id: int):
    # Register worker in not already in the user notifications dictionary
    if request_id not in user_notifications:
        user_notifications[request_id] = []
        
    # Start streaming user notifications
    return StreamingResponse(event_stream_user(request_id), media_type="text/event-stream")
