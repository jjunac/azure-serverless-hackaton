import logging
import time
import uuid
import requests
from typing import Optional
import azure.functions as func
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as cosmos_exceptions

from azure.cosmos.partition_key import PartitionKey

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


DB_HOST = "https://openhackdb.documents.azure.com:443/"
DB_MASTER_KEY = "GYslGRpMOdHh9eHfR412sV4Cr5UU3DgeL8jHQ9pLnYXUChGw3GBFCExnWwxTOW3SwqVgmLxyR243TjCfJTbSUQ=="
DB_DATABASE_ID = "rating"
DB_CONTAINER_ID = "ratingcontainer"

db_client = cosmos_client.CosmosClient(DB_HOST, {'masterKey': DB_MASTER_KEY} )
rating_container = db_client.create_database_if_not_exists(id=DB_DATABASE_ID).create_container_if_not_exists(id=DB_CONTAINER_ID, partition_key=PartitionKey(path='/id', kind='Hash'))

app = FastAPI()


def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    return func.AsgiMiddleware(app).handle(req, context)


def user_exists(userId: str) -> bool:
    res = requests.get('https://serverlessohapi.azurewebsites.net/api/GetUser', params={"userId": userId})
    print(res)
    return res.status_code == 200


def product_exists(productId: str) -> bool:
    res = requests.get('https://serverlessohapi.azurewebsites.net/api/GetProduct', params={"productId": productId})
    print(res)
    return res.status_code == 200


class Rating(BaseModel):
    userId: str
    productId: str
    locationName: str
    rating: int
    userNotes: str


@app.post("/CreateRating")
def post_rating(rating: Rating):
    print("Received rating:", rating)
    if not (0 <= rating.rating and rating.rating <= 5):
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"error": f"Parameter 'rating is '{rating.rating}', which is not between 0 and 5"})
    if not user_exists(rating.userId) or not product_exists(rating.productId):
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"error": f"Parameter 'userId' or 'productId' doesn't exists"})
    inserted_rating = rating_container.create_item(body={
        "id": str(uuid.uuid4()),
        "timestamp": int(time.time()),
        **dict(rating)
    })
    return JSONResponse(content=inserted_rating)


@app.get("/GetRating")
@app.get("/GetRating/{ratingId}")
def get_rating_by_id(ratingId: Optional[str] = None):
    print("Received ratingId:", ratingId)
    if not ratingId:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"error": "Missing mandatory parameter 'ratingId'"})
    try:
        rating = rating_container.read_item(item=ratingId, partition_key=ratingId)
        print("Retrieved rating:", rating)
        return JSONResponse(content=rating)
    except cosmos_exceptions.CosmosResourceNotFoundError:
        print("Rating not found")
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": f"Rating not found for id '{ratingId}'"})


@app.get("/GetRatings")
@app.get("/GetRatings/{userId}")
def get_ratings_by_user(userId: Optional[str] = None):
    print("Received userId:", userId)
    if not userId:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"error": "Missing mandatory parameter 'userId'"})
    if not user_exists(userId):
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"error": f"Parameter 'userId' doesn't exists"})
    rating_list = list(rating_container.query_items(
        query="SELECT * FROM rating WHERE rating.userId=@userId",
        parameters=[
            { "name":"@userId", "value": userId }
        ],
        enable_cross_partition_query=True
    ))
    print("Retrieved ratings:", rating_list)
    return JSONResponse(content=rating_list)

