from fastapi import FastAPI

app = FastAPI(title="Rel360 API")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Rel360 API activa"}
