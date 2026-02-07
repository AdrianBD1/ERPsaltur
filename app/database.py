import pandas as pd
import os
from datetime import datetime
import uuid

DATA_DIR = "data"
PRODUCTOS_FILE = os.path.join(DATA_DIR, "PRODUCTOS_BD.csv")
COMPRAS_FILE = os.path.join(DATA_DIR, "COMPRAS_BD.csv")
VENTAS_FILE = os.path.join(DATA_DIR, "VENTAS_BD.csv")

# Asegurar que existan los archivos
def init_db():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    if not os.path.exists(PRODUCTOS_FILE):
        pd.DataFrame(columns=[
            "id", "nombre", "precio_compra", "precio_venta", 
            "categoria", "tipo", "unidad", "proveedor", "stock", "ubicacion"
        ]).to_csv(PRODUCTOS_FILE, index=False)

    if not os.path.exists(COMPRAS_FILE):
        pd.DataFrame(columns=["id", "fecha_compra", "precio_compra", "cantidad", "total"]).to_csv(COMPRAS_FILE, index=False)

    if not os.path.exists(VENTAS_FILE):
        pd.DataFrame(columns=["id", "fecha_venta", "precio_venta", "cantidad", "total"]).to_csv(VENTAS_FILE, index=False)

def get_productos():
    return pd.read_csv(PRODUCTOS_FILE).fillna("")

def get_producto_by_id(prod_id):
    df = get_productos()
    item = df[df['id'] == prod_id]
    return item.iloc[0].to_dict() if not item.empty else None

def buscar_productos(query):
    df = get_productos()
    # Filtra si el query está en el nombre (ignorando mayúsculas/minúsculas)
    result = df[df['nombre'].str.contains(query, case=False, na=False)]
    return result.to_dict(orient="records")

def registrar_compra_batch(items):
    # items es una lista de diccionarios con los datos del formulario
    df_prod = get_productos()
    df_compras = pd.read_csv(COMPRAS_FILE)
    
    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for item in items:
        prod_id = item.get('id')
        nombre = item['nombre']
        cantidad = float(item['cantidad'])
        precio_compra = float(item['precio_compra'])
        total = cantidad * precio_compra
        
        # Si es producto nuevo (no tiene ID o ID no existe)
        if not prod_id or prod_id not in df_prod['id'].values:
            prod_id = str(uuid.uuid4())[:8] # ID corto
            nuevo_prod = {
                "id": prod_id, "nombre": nombre, "precio_compra": precio_compra,
                "precio_venta": 0, "categoria": "General", "tipo": "General",
                "unidad": "unidad", "proveedor": "General", "stock": cantidad, "ubicacion": "Bodega"
            }
            df_prod = pd.concat([df_prod, pd.DataFrame([nuevo_prod])], ignore_index=True)
        else:
            # Actualizar stock y precio de compra último
            idx = df_prod.index[df_prod['id'] == prod_id][0]
            df_prod.at[idx, 'stock'] += cantidad
            df_prod.at[idx, 'precio_compra'] = precio_compra # Actualizamos costo

        # Registrar en historial
        nueva_compra = {
            "id": prod_id, "fecha_compra": fecha_hoy, 
            "precio_compra": precio_compra, "cantidad": cantidad, "total": total
        }
        df_compras = pd.concat([df_compras, pd.DataFrame([nueva_compra])], ignore_index=True)

    df_prod.to_csv(PRODUCTOS_FILE, index=False)
    df_compras.to_csv(COMPRAS_FILE, index=False)
    return True

def registrar_venta_batch(items):
    df_prod = get_productos()
    df_ventas = pd.read_csv(VENTAS_FILE)
    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for item in items:
        prod_id = item.get('id')
        cantidad = float(item['cantidad'])
        precio_venta = float(item['precio_venta']) # Usamos el precio definido en el momento
        total = cantidad * precio_venta

        if prod_id in df_prod['id'].values:
            idx = df_prod.index[df_prod['id'] == prod_id][0]
            current_stock = df_prod.at[idx, 'stock']
            # Permitimos stock negativo? Asumiremos que sí por simplicidad, o podrías bloquearlo
            df_prod.at[idx, 'stock'] = current_stock - cantidad
            
            nueva_venta = {
                "id": prod_id, "fecha_venta": fecha_hoy,
                "precio_venta": precio_venta, "cantidad": cantidad, "total": total
            }
            df_ventas = pd.concat([df_ventas, pd.DataFrame([nueva_venta])], ignore_index=True)

    df_prod.to_csv(PRODUCTOS_FILE, index=False)
    df_ventas.to_csv(VENTAS_FILE, index=False)
    return True

def get_historial(tipo="compras"):
    df_prod = get_productos()[['id', 'nombre']]
    if tipo == "compras":
        df_hist = pd.read_csv(COMPRAS_FILE)
    else:
        df_hist = pd.read_csv(VENTAS_FILE)
    
    # Unir con productos para tener el nombre
    merged = pd.merge(df_hist, df_prod, on='id', how='left')
    return merged.fillna("Producto Eliminado").to_dict(orient="records")

def get_top_ventas(dias):
    df_ventas = pd.read_csv(VENTAS_FILE)
    df_prod = get_productos()
    
    # Convertir fechas
    df_ventas['fecha_venta'] = pd.to_datetime(df_ventas['fecha_venta'])
    cutoff = pd.to_datetime(datetime.now()) - pd.Timedelta(days=int(dias))
    
    filtrado = df_ventas[df_ventas['fecha_venta'] >= cutoff]
    
    # Agrupar
    agrupado = filtrado.groupby('id').agg({
        'cantidad': 'sum',
        'total': 'sum' # Total vendido
    }).reset_index()
    
    # Unir info producto para calcular ganancia (Total Venta - (Costo Actual * Cantidad))
    merged = pd.merge(agrupado, df_prod[['id', 'nombre', 'precio_compra']], on='id', how='left')
    
    merged['ganancia'] = merged['total'] - (merged['precio_compra'] * merged['cantidad'])
    
    return merged.to_dict(orient="records")