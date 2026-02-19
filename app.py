from fastapi import FastAPI

app = FastAPI(
    title="FastAPI",
    description="FastAPI",
    version="0.1.0",
)

import fastapi_cdn_host

fastapi_cdn_host.patch_docs(app)

from api.v1 import v1Router

app.include_router(v1Router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8020)
