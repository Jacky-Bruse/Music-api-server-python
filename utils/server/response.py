from fastapi.responses import ORJSONResponse


def handleResponse(body: dict) -> ORJSONResponse:
    status = body.get("code", 200)
    return ORJSONResponse(
        body, status_code=status, headers={"Access-Control-Allow-Origin": "*"}
    )
