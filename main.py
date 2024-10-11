from fastapi import FastAPI
from users.views import user_router
from workers.views import worker_router
from auth.views import auth_router
from search_workers.views import search_workers_router


app = FastAPI()


## Register the user router
app.include_router(user_router)

## Register the worker router
app.include_router(worker_router)

## Register the auth router
app.include_router(auth_router)

## Register the search workers router
app.include_router(search_workers_router)

