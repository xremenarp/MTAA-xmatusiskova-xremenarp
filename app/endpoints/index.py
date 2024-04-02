import decimal
from datetime import datetime, timezone

import psycopg2.pool
from fastapi import APIRouter

from app.config import settings

router = APIRouter()

pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dbname=settings.DATABASE_NAME,
    host=settings.DATABASE_HOST,
    port=settings.DATABASE_PORT,
    user=settings.DATABASE_USER,
    password=settings.DATABASE_PASSWORD
)

def serialize_datetime_and_decimal(obj):
    if isinstance(obj, datetime):
        return obj.astimezone(timezone.utc).isoformat(timespec='milliseconds')[:-3]
    elif isinstance(obj, (float, decimal.Decimal)):
        return float(obj)
    else:
        return obj

def zip_objects_from_db(data, cursor):
    return [dict(zip((key[0] for key in cursor.description),
                     [serialize_datetime_and_decimal(value) for value in row])) for row in data]

@router.get("/hello")
async def hello() -> dict:
    return {
        'hello': settings.DATABASE_NAME
    }


@router.get("/status")
async def status() -> dict:
    conn = pool.getconn()
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    cursor.close()
    pool.putconn(conn)
    return {
        'version': version
    }
@router.post("/api/login/{username}/{password}")
async def login(username: str, password: str) -> dict:
    conn = pool.getconn()
    cursor = conn.cursor()
    query = ("""SELECT username, password
                FROM users
                WHERE username= %s AND password= %s""")
    cursor.execute(query, (username, password))
    record = cursor.fetchone()
    cursor.close()
    pool.putconn(conn)

    if (record[0] == username and record[1] == password):
        return {"status": True}
    else:
        return {"status": False}

@router.post("/api/signup/{username}/{password}")
async def signup(username: str, password: str) -> dict:
    conn = pool.getconn()
    cursor = conn.cursor()
    query = ("""INSERT INTO users
                VALUES (%s,%s)""")
    cursor.execute(query, (username, password))
    cursor.close()
    pool.putconn(conn)
    return {"status": "Done"}

# global_username = ""

@router.get("/api/forgotten-password/{username}")
async def forgotten(username: str) -> dict:
    conn = pool.getconn()
    cursor = conn.cursor()
    query = ("""SELECT username
                FROM users
                WHERE username= %s """)
    cursor.execute(query, (username))

    record = cursor.fetchone()
    global global_username
    global_username = username
    cursor.close()
    pool.putconn(conn)

    if (record[0] == username):
        return {"status": True}
    else:
        return {"status": False}

@router.put("/api/reset-password/{password}")
async def reset(password: str) -> dict:
    conn = pool.getconn()
    cursor = conn.cursor()
    query = ("""UPDATE users
                SET password = %s
                WHERE username = %s """)
    cursor.execute(query, (global_username, password))
    cursor.close()
    pool.putconn(conn)
    return {"status": True}

@router.get("/api/activities")
async def activities() -> dict:
    conn = pool.getconn()
    cursor = conn.cursor()
    query = ("""SELECT *
                FROM activities""")
    cursor.execute(query)

    data = cursor.fetchone()
    records = zip_objects_from_db(data, cursor)

    cursor.close()
    pool.putconn(conn)
    return {"items": records}
