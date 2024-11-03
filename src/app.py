from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes.graph_crud_routes import router as graph_crud_router
from src.routes.graph_run_routes import router as graph_run_router
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

app = FastAPI(title="Graph Processing API", version="1.0")

# Load environment variables from .env file
load_dotenv()

# Retrieve the MongoDB URI from the .env file
MONGO_URI = os.getenv("MONGO_URI")

# Create an AsyncIOMotorClient instance
client = AsyncIOMotorClient(MONGO_URI)

# Access the "graph_database" database
db = client["graph_database"]

# Include different routers from the modules to organize the endpoints
app.include_router(graph_crud_router, prefix="/api", tags=["Graph CRUD Operations"])
app.include_router(graph_run_router, prefix="/api", tags=["Graph Run Operations"])

@app.on_event("startup")
async def startup_event():
    try:
        # Attempt a command to test the connection
        server_info = await client.server_info()
        print("Connected to MongoDB")
    except Exception as e:
        print("Could not connect to MongoDB:", e)

@app.get("/", summary="Root Endpoint")
async def root():
    return {"message": "Welcome to the Graph Processing API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
