from fastapi import FastAPI


app = FastAPI(
    title="OrderFlow API",
    description="Distributed Order Processing Backend",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "orderflow",
    }