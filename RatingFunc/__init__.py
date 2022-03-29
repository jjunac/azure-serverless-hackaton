import logging
from typing import Optional
import azure.functions as func

from fastapi import FastAPI

app = FastAPI()

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    return func.AsgiMiddleware(app).handle(req, context)


@app.get("/ratings")
def get_product(productId: Optional[str] = None):
    return f"hello everyone"

