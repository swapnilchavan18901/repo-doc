from fastapi import APIRouter
from fastapi.responses import Response
from markdown2 import Markdown

router = APIRouter()


@router.get("dinkachika/", response_class=Response)
def index() -> Response:
    return Response("Hello, World!")
