from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import app.database as db

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Inicializar DB al arrancar
db.init_db()

# Modelos para recibir datos JSON
class ItemOperacion(BaseModel):
    id: Optional[str] = None
    nombre: Optional[str] = None
    precio_compra: Optional[float] = 0.0
    precio_venta: Optional[float] = 0.0
    cantidad: float
    total: float

# --- Vistas HTML ---
@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/registrar/compra")
def view_compra(request: Request):
    return templates.TemplateResponse("form_compra.html", {"request": request})

@app.get("/registrar/venta")
def view_venta(request: Request):
    return templates.TemplateResponse("form_venta.html", {"request": request})

@app.get("/ver/productos")
def view_productos(request: Request):
    datos = db.get_productos().to_dict(orient="records")
    return templates.TemplateResponse("tabla.html", {
        "request": request, "datos": datos, "titulo": "Inventario de Productos", "tipo": "inventario"
    })

@app.get("/ver/historial/{tipo}")
def view_historial(request: Request, tipo: str):
    datos = db.get_historial(tipo)
    titulo = "Historial de Compras" if tipo == "compras" else "Historial de Ventas"
    return templates.TemplateResponse("tabla.html", {
        "request": request, "datos": datos, "titulo": titulo, "tipo": tipo
    })

@app.get("/ver/top")
def view_top(request: Request):
    return templates.TemplateResponse("top_ventas.html", {"request": request})

# --- API Endpoints (AJAX) ---
@app.get("/api/buscar-producto")
def api_buscar(q: str):
    return db.buscar_productos(q)

@app.post("/api/registrar-compra")
def api_reg_compra(items: List[ItemOperacion]):
    db.registrar_compra_batch([i.dict() for i in items])
    return {"status": "ok"}

@app.post("/api/registrar-venta")
def api_reg_venta(items: List[ItemOperacion]):
    db.registrar_venta_batch([i.dict() for i in items])
    return {"status": "ok"}

@app.get("/api/top-ventas")
def api_top_ventas(dias: int):
    return db.get_top_ventas(dias)