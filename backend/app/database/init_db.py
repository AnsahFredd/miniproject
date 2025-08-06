# app/database/init_db.py

from fastapi import FastAPI
from app.database.mongo import connect_to_mongo, close_mongo_connection

def register_db(app: FastAPI):
    @app.on_event("startup")
    async def startup():
        await connect_to_mongo()

    @app.on_event("shutdown")
    async def shutdown():
        await close_mongo_connection()
