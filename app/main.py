from fastapi import FastAPI

app = FastAPI(title="School Portal Platform")

@app.get("/health")
async def health_check():
    return {"status": "ok"}