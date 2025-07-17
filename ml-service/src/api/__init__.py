from .mlflow_api import router as mlflow_router
from .health import router as health_router
from .root import router as root_router

all_routers = [
    mlflow_router,
    health_router,
    root_router
]
