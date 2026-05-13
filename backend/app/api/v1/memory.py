from fastapi import APIRouter

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/search")
async def memory_search_placeholder() -> dict:
    return {"hits": []}
