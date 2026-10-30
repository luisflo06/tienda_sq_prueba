import logging
import os
import sqlite3
from contextlib import closing

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

app = FastAPI()

# CORS restringido a los orígenes que realmente necesitas (configurable por entorno)
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["Content-Type"],
)

# Los secretos NUNCA van en el código: se leen de variables de entorno
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
DB_NAME = os.environ.get("DB_NAME", "tienda_exotica.db")

PRODUCTOS_INICIALES = [
    (1, "Perfume 212 Men NYC", 350000, "https://cdn-icons-png.flaticon.com/512/3058/3058866.png"),
    (2, "Auriculares KZ EDX Pro", 85000, "https://cdn-icons-png.flaticon.com/512/2619/2619726.png"),
    (3, "Loción Temptation Men", 120000, "https://cdn-icons-png.flaticon.com/512/3058/3058866.png"),
    (4, "Mouse Gamer RGB", 95000, "https://cdn-icons-png.flaticon.com/512/1231/1231698.png"),
]


def inicializar_bd() -> None:
    # closing() garantiza que la conexión se cierre aunque haya errores
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:  # commit / rollback automático
            conn.execute(
                "CREATE TABLE IF NOT EXISTS productos "
                "(id INTEGER PRIMARY KEY, nombre TEXT, precio REAL, imagen TEXT)"
            )
            total = conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
            if total == 0:
                conn.executemany(
                    "INSERT INTO productos (id, nombre, precio, imagen) VALUES (?, ?, ?, ?)",
                    PRODUCTOS_INICIALES,
                )


inicializar_bd()


@app.get("/api/productos")
def obtener_productos(busqueda: str = Query("", max_length=100)):
    # Consulta parametrizada: evita la inyección SQL
    patron = f"%{busqueda}%"
    try:
        with closing(sqlite3.connect(DB_NAME)) as conn:
            filas = conn.execute(
                "SELECT id, nombre, precio, imagen FROM productos WHERE nombre LIKE ?",
                (patron,),
            ).fetchall()
    except sqlite3.Error:
        # Se registra el error real y se responde con un error HTTP adecuado
        logger.exception("Error consultando productos")
        raise HTTPException(status_code=500, detail="Error interno al consultar productos")

    productos = [
        {"id": f[0], "nombre": f[1], "precio": f[2], "imagen": f[3]} for f in filas
    ]
    return {"success": True, "productos": productos}