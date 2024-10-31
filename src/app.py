from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes.graph_crud_routes import router as graph_crud_router
from src.routes.graph_run_routes import router as graph_run_router

app = FastAPI(title="Graph Processing API", version="1.0")

# Set up CORS Middleware to allow cross-origin requests from the frontend
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include different routers from the modules to organize the endpoints
app.include_router(graph_crud_router, prefix="/api/graph", tags=["Graph CRUD Operations"])
app.include_router(graph_run_router, prefix="/api/graph", tags=["Graph Run Operations"])

@app.get("/", summary="Root Endpoint")
async def root():
    return {"message": "Welcome to the Graph Processing API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
