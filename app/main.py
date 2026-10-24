from fastapi import FastAPI

app = FastAPI(title="GramSetu API")

@app.get("/")
def home():
    return {"message": "Welcome to GramSetu"}