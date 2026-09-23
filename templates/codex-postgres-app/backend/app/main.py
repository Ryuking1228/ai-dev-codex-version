import os
from pathlib import Path
from typing import Annotated
from uuid import UUID

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from psycopg.rows import dict_row
from starlette.exceptions import HTTPException as StarletteHTTPException

def problem_response(description):
    return {"description": description, "content": {"application/problem+json": {
        "schema": {"$ref": "#/components/schemas/Problem"}}}}


app = FastAPI(title="__APP_NAME__", responses={
    503: problem_response("Database unavailable"),
    422: problem_response("Invalid input"),
})


class Problem(BaseModel):
    type: str
    title: str
    status: int


class Health(BaseModel):
    status: str


class ItemInput(BaseModel):
    title: str = Field(min_length=1, max_length=120)

    @field_validator("title")
    @classmethod
    def normalize(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Title must not be blank")
        return value


class Item(BaseModel):
    id: UUID
    title: str


class PostgresItems:
    def connection(self):
        return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row, connect_timeout=5)

    def list(self):
        with self.connection() as conn:
            return conn.execute("SELECT id, title FROM items ORDER BY created_at, id").fetchall()

    def create(self, title):
        with self.connection() as conn:
            return conn.execute("INSERT INTO items(title) VALUES (%s) RETURNING id, title", (title,)).fetchone()

    def delete(self, item_id):
        with self.connection() as conn:
            return conn.execute("DELETE FROM items WHERE id = %s", (item_id,)).rowcount > 0


def repository():
    return PostgresItems()


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    return JSONResponse({"type": "about:blank", "title": str(exc.detail), "status": exc.status_code},
                        status_code=exc.status_code, media_type="application/problem+json")


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse({"type": "about:blank", "title": "Invalid input", "status": 422},
                        status_code=422, media_type="application/problem+json")


@app.exception_handler(psycopg.Error)
async def database_error(request: Request, exc: psycopg.Error):
    return JSONResponse({"type": "about:blank", "title": "Database unavailable", "status": 503},
                        status_code=503, media_type="application/problem+json")


@app.get("/api/health", response_model=Health, operation_id="health")
def health():
    with repository().connection() as conn:
        conn.execute("SELECT 1 FROM items LIMIT 1")
    return {"status": "ok"}


@app.get("/api/items", response_model=list[Item], operation_id="listItems")
def list_items(repo: Annotated[PostgresItems, Depends(repository)]):
    return repo.list()


@app.post("/api/items", response_model=Item, status_code=201, operation_id="createItem")
def create_item(item: ItemInput, repo: Annotated[PostgresItems, Depends(repository)]):
    return repo.create(item.title)


@app.delete("/api/items/{item_id}", status_code=204, operation_id="deleteItem",
            responses={404: problem_response("Item not found")})
def delete_item(item_id: UUID, repo: Annotated[PostgresItems, Depends(repository)]):
    if not repo.delete(item_id):
        raise HTTPException(404, "Item not found")


def openapi():
    if app.openapi_schema is None:
        schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
        schema.setdefault("components", {}).setdefault("schemas", {})["Problem"] = Problem.model_json_schema()
        app.openapi_schema = schema
    return app.openapi_schema


app.openapi = openapi


static_root = Path(os.environ.get("STATIC_DIR", "frontend/dist"))
if static_root.is_dir():
    app.mount("/", StaticFiles(directory=static_root, html=True), name="frontend")
