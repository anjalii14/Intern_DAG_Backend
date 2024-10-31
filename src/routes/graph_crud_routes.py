from fastapi import APIRouter, HTTPException
from src.controllers.graph_controller import create_graph, get_graph, update_graph, delete_graph
from src.models.graph_model import Graph
from typing import Dict, Any

router = APIRouter()

@router.post("/graph", response_model=Dict[str, Any])
async def create_graph_route(graph: Graph):
    """Create a new graph."""
    try:
        created_graph = await create_graph(graph)
        return created_graph
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/graph/{graph_id}", response_model=Graph)
async def get_graph_route(graph_id: str):
    """Retrieve a graph by its ID."""
    try:
        return await get_graph(graph_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/graph/{graph_id}", response_model=Graph)
async def update_graph_route(graph_id: str, updated_graph: Graph):
    """Update an existing graph by ID."""
    try:
        return await update_graph(graph_id, updated_graph)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/graph/{graph_id}", response_model=Dict[str, bool])
async def delete_graph_route(graph_id: str):
    """Delete a graph by its ID."""
    try:
        result = await delete_graph(graph_id)
        return {"success": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
