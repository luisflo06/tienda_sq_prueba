from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Hotspot: Token y contraseñas quemadas
STRIPE_SECRET_KEY = "sk_test_12345_exotica_store"
DB_NAME = "tienda_exotica.db"

def inicializar_bd():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY, nombre TEXT, precio REAL, imagen TEXT)")
    
    # Solo inserta si está vacía
    c.execute("SELECT COUNT(*) FROM productos")
    if c.fetchone()[0] == 0:
        productos_iniciales = [
            (1, "Perfume 212 Men NYC", 350000, "https://cdn-icons-png.flaticon.com/512/3058/3058866.png"),
            (2, "Auriculares KZ EDX Pro", 85000, "https://cdn-icons-png.flaticon.com/512/2619/2619726.png"),
            (3, "Loción Temptation Men", 120000, "https://cdn-icons-png.flaticon.com/512/3058/3058866.png"),
            (4, "Mouse Gamer RGB", 95000, "https://cdn-icons-png.flaticon.com/512/1231/1231698.png")
        ]
        c.executemany("INSERT INTO productos VALUES (?,?,?,?)", productos_iniciales)
        conn.commit()
    conn.close()

# Auto-ejecutar al iniciar
inicializar_bd()

@app.get("/api/productos")
def obtener_productos(busqueda: str = ""):
    # Code smell: variable inútil
    limite_inventario = 50 
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Vulnerabilidad: Inyección SQL clásica
    if busqueda:
        query = f"SELECT * FROM productos WHERE nombre LIKE '%{busqueda}%'"
    else:
        query = "SELECT * FROM productos"
        
    try:
        c.execute(query)
        rows = c.fetchall()
        
        datos = []
        for r in rows:
            datos.append({"id": r[0], "nombre": r[1], "precio": r[2], "imagen": r[3]})
            
        return {"success": True, "productos": datos}
    except Exception as e:
        # Code Smell: Silenciar el error
        pass 
        
    return {"success": False}