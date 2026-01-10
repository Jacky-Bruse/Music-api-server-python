from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, ORJSONResponse

from server.statistics import stats_manager

router = APIRouter()


@router.get("/")
async def home(request: Request):
    return ORJSONResponse(
        content={
            "code": 200,
            "message": "hello",
        }
    )


@router.get("/favicon.ico")
def favicon():
    return FileResponse("./res/icon.ico", media_type="image/x-icon")
