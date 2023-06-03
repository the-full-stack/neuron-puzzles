from pathlib import Path

import modal
from modal import asgi_app, Mount

from app.common import image, stub

assets_path = Path(__file__).parent.parent.resolve() / "static"


@stub.function(
    image=image,
    mounts=[
        Mount.from_local_dir(assets_path, remote_path="/assets"),
        *modal.create_package_mounts(["app.common", "app.data"]),
    ],
    container_idle_timeout=300,
    timeout=600,
    secrets=[modal.Secret.from_name("mongodb-neuron-puzzles")],
)
@asgi_app()
def web():
    import os
    from typing import List

    from fastapi import FastAPI, Body
    from fastapi.responses import Response
    from fastapi.staticfiles import StaticFiles
    import motor.motor_asyncio
    from pydantic import BaseModel

    from app.data import models

    web_app = FastAPI(title="Neuron Puzzles")
    connection_string = _get_connection_string()
    client = motor.motor_asyncio.AsyncIOMotorClient(connection_string)
    db = client[os.environ["MONGODB_DBNAME"]]

    class HealthyResponse(BaseModel):
        status: str

        class Config:
            schema_extra = {
                "example": {
                    "status": "200 more like 💯 mirite",
                }
            }

    @web_app.get(
        "/health",
        response_description="If you get this response, the server is healthy.",
        name="Health check",
        operation_id="health",
        response_model=HealthyResponse,
        tags=["internal"],
    )
    async def health() -> HealthyResponse:
        """Check the vibes."""
        return {"status": "200 more like 💯 mirite"}

    @web_app.get(
        "/puzzles",
        response_description="Puzzles with basic information",
        name="List all puzzles",
        status_code=200,
        response_model=List[models.PuzzleBasics],
        tags=["puzzles"],
    )
    async def list_puzzles() -> List[models.PuzzleBasics]:
        """Retrieve a list of all puzzles."""
        puzzles = []
        async for puzzle in db.puzzles.find({}, projection={"activationRecords": 0}):
            puzzle["_id"] = models.ObjectId(puzzle["_id"])
            puzzles.append(models.PuzzleBasics(**puzzle))
        return puzzles

    @web_app.get(
        "/puzzles/{puzzle_id}",
        response_description="A single puzzle, including its activation records",
        status_code=200,
        response_model=models.Puzzle,
        tags=["puzzles"],
    )
    async def get_puzzle(puzzle_id: str) -> models.Puzzle:
        """Get a single puzzle using its identifier."""
        import bson

        try:
            puzzle = await db.puzzles.find_one({"_id": models.ObjectId(puzzle_id)})
        except bson.errors.InvalidId:
            return Response(
                status_code=418,
                content="Invalid puzzle ID",
                headers={"content-type": "text/plain"},
            )

        if puzzle:
            return models.Puzzle(**puzzle)

        return Response(status_code=404)

    @web_app.post(
        "/answer",
        response_description="A copy of the answer, now with an identifier",
        status_code=201,
        response_model=models.Answer,
        tags=["answers"],
    )
    async def create_answer(answer: models.UpdateAnswer = Body(...)) -> models.Answer:
        """Add a user's answer to the database."""
        answer.puzzleId = models.ObjectId(answer.puzzleId)
        answer.choiceId = models.ObjectId(answer.choiceId)

        answer = await db.answers.insert_one(answer.dict())
        inserted_answer = await db.answers.find_one({"_id": answer.inserted_id})

        return models.Answer(**inserted_answer)

    web_app.mount("/", StaticFiles(directory="/assets", html=True))

    return web_app


def _get_connection_string():
    import os

    user = os.environ["MONGODB_USER"]
    password = os.environ["MONGODB_PASSWORD"]
    host = os.environ["MONGODB_HOST"]

    return f"mongodb+srv://{user}:{password}@{host}/?retryWrites=true&w=majority"
