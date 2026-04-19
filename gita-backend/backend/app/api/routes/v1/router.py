import importlib.metadata

from fastapi import APIRouter

from app.api.routes.v1 import guidance, retrieval

router = APIRouter(tags=["v1"])


@router.get("/version")
def api_version() -> dict[str, str]:
    try:
        version = importlib.metadata.version("gita-backend")
    except importlib.metadata.PackageNotFoundError:
        version = "0.0.0"
    return {"api": "v1", "package_version": version}


router.include_router(guidance.router)
router.include_router(retrieval.router)
