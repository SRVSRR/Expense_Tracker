from dotenv import load_dotenv

load_dotenv()

from app.factory import create_app  # noqa: E402

app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)