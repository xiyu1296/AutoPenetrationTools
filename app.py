from fastapi import FastAPI

app = FastAPI(
    title="FastAPI",
    description="FastAPI",
    version="0.1.0",
    servers=[
        {"url": "http://localhost:8020", "description": "本地访问"},
        {"url": "http://127.0.0.1:8020", "description": "本地IP访问"},
        {"url": "http://host.docker.internal:8020", "description": "Docker内部访问"}
    ]
)

import fastapi_cdn_host

fastapi_cdn_host.patch_docs(app)

from api.v1 import v1Router

app.include_router(v1Router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8020)
