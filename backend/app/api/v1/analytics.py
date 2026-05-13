from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def analytics_summary() -> dict:
    return {"tasks_today": 0, "success_rate": None}
