from api.ml_api_server import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.ml_api_server:app", host="0.0.0.0", port=8002, reload=False) 