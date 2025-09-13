# app.py — Monolito: Front (HTML + CSS + JS) + API + DB (PostgreSQL)
# Executar: python app.py
# Auto-setup:
# 1) cria o DATABASE se não existir;
# 2) cria o SCHEMA (padrão: carshop) se não existir;
# 3) cria a TABELA cars no schema se não existir.

import subprocess, sys, os
from typing import Optional

# ---------- Auto-instalação de dependências ----------
REQUIRED = ["fastapi", "uvicorn[standard]", "sqlalchemy", "pydantic", "psycopg2-binary"]
def ensure_packages(pkgs):
    for pkg in pkgs:
        try:
            __import__(pkg.split("[")[0])
        except ImportError:
            print(f"[SETUP] Instalando {pkg} ...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
ensure_packages(REQUIRED)

# ---------- Importes após garantir libs ----------
from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy import create_engine, Column, Integer, String, Numeric, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine.url import make_url
from sqlalchemy import inspect as sa_inspect

# ---------- Config do banco (PostgreSQL) ----------
DEFAULT_PG_URL = "postgresql+psycopg2://postgres@localhost:5432/carshop"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_PG_URL)

if DATABASE_URL.startswith("sqlite"):
    raise RuntimeError("SQLite não é permitido. Use PostgreSQL (DATABASE_URL postgresql+psycopg2://...).")

# Nome do schema (padrão 'carshop'); pode trocar via variável de ambiente DB_SCHEMA
SCHEMA_NAME = os.getenv("DB_SCHEMA", "carshop")

def ensure_database(db_url_str: str):
    """Cria o database alvo se não existir, conectando-se ao DB 'postgres'."""
    url = make_url(db_url_str)
    target_db = url.database
    admin_url = url.set(database="postgres")
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT", future=True)

    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": target_db}
        ).scalar()
        if not exists:
            print(f"[SETUP] Criando database '{target_db}' ...")
            conn.execute(text(f'CREATE DATABASE "{target_db}"'))
    admin_engine.dispose()

# 1) Garante database
ensure_database(DATABASE_URL)

# Conecta no database alvo
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

# 2) Garante schema
def ensure_schema(schema: str):
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        # opcional: definir search_path (não é obrigatório, pois o modelo usa schema)
        # conn.execute(text(f"SET search_path TO {schema}, public"))

ensure_schema(SCHEMA_NAME)

# ---------- Modelo (com schema explícito) ----------
class Car(Base):
    __tablename__ = "cars"
    __table_args__ = {"schema": SCHEMA_NAME}  # <— TABELA NO SCHEMA carshop
    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String(60), nullable=False)
    model = Column(String(80), nullable=False)
    year = Column(Integer, nullable=False)
    color = Column(String(40), default="")
    mileage_km = Column(Integer, default=0)
    price = Column(Numeric(12, 2), nullable=False)
    quantity = Column(Integer, default=0)
    status = Column(String(12), default="Ativo")  # Ativo / Inativo

# 3) Garante tabela
def ensure_table():
    insp = sa_inspect(engine)
    # Verifica se a tabela 'cars' existe no schema informado
    if not insp.has_table("cars", schema=SCHEMA_NAME):
        print(f"[SETUP] Criando tabela {SCHEMA_NAME}.cars ...")
        Base.metadata.create_all(bind=engine, tables=[Car.__table__])
    else:
        # garante que eventuais ajustes de metadados não quebrem; normalmente não precisam
        Base.metadata.create_all(bind=engine, tables=[Car.__table__])

ensure_table()

# ---------- App ----------
app = FastAPI(title="CarShop • Impacta (PostgreSQL, auto-setup com schema)")

# ---------- HTML ----------
HTML_PAGE = """<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <title>CarShop • Impacta</title>
  <link rel="stylesheet" href="/assets/styles.css">
  <meta name="viewport" content="width=device-width, initial-scale=1" />
</head>
<body>
  <div class="container">
    <h1>CarShop • Impacta</h1>

    <h2>Cadastro / Edição</h2>
    <form id="carForm" class="card">
      <input type="hidden" id="carId">
      <div class="grid">
        <!-- Coluna 1 -->
        <div class="field">
          <label for="brand">Marca</label>
          <input id="brand" required placeholder="Ex.: Toyota">
        </div>
        <div class="field">
          <label for="model">Modelo</label>
          <input id="model" required placeholder="Ex.: Corolla">
        </div>
        <div class="field">
          <label for="year">Ano</label>
          <input type="number" id="year" required placeholder="Ex.: 2020" min="1900" max="2100">
        </div>
        <div class="field">
          <label for="color">Cor</label>
          <input id="color" placeholder="Ex.: Prata">
        </div>

        <!-- Coluna 2 -->
        <div class="field">
          <label for="mileage_km">KM</label>
          <input type="number" id="mileage_km" value="0" min="0" step="1">
        </div>
        <div class="field">
          <label for="price">Preço</label>
          <input type="number" id="price" step="0.01" required placeholder="Ex.: 98000.00" min="0">
        </div>
        <div class="field">
          <label for="quantity">Quantidade</label>
          <input type="number" id="quantity" value="0" min="0" step="1">
        </div>
        <div class="field">
          <label for="status">Status</label>
          <select id="status">
            <option value="Ativo" selected>Ativo</option>
            <option value="Inativo">Inativo</option>
          </select>
        </div>

        <!-- Ações -->
        <div class="actions" style="grid-column: 1 / -1; margin-top: 4px;">
          <button type="submit" class="btn-primary">Salvar</button>
          <button type="button" id="btnNew" class="btn-secondary">Novo</button>
        </div>
      </div>
    </form>

    <h2>Catálogo</h2>
    <div class="card">
      <div class="toolbar" style="margin-bottom:10px;">
        <input id="filterBrand" placeholder="Filtrar por marca (Ex.: Toyota)" style="flex:1;">
        <button id="btnFilter" class="btn-secondary">Filtrar</button>
        <button id="btnClear" class="btn-secondary">Limpar</button>
      </div>

      <table id="carsTable">
        <thead>
          <tr>
            <th>ID</th><th>Marca</th><th>Modelo</th><th>Ano</th>
            <th>Cor</th><th>KM</th><th>Preço</th><th>Qtd</th><th>Status</th><th>Ações</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
  </div>

  <script src="/assets/app.js"></script>
</body>
</html>
"""

# ---------- CSS ----------
CSS_STYLES = """
:root { --gap: 12px; }
* { box-sizing: border-box; }
body { font-family: Arial, sans-serif; margin: 24px; color:#111; background:#fff; }
.container { max-width: 1100px; margin: 0 auto; }
h1 { margin: 0 0 16px; }
h2 { margin: 24px 0 12px; }
.card { border:1px solid #e5e5e5; border-radius:12px; padding:16px; box-shadow:0 2px 6px rgba(0,0,0,.04); background:#fff; }
.grid { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--gap); }
.field { display:flex; flex-direction:column; gap:6px; }
label { font-size:13px; color:#444; }
input, select, button { padding:10px 12px; border:1px solid #d9d9d9; border-radius:8px; background:#fff; }
input:focus, select:focus { outline: none; border-color:#2563eb; box-shadow:0 0 0 3px rgba(37,99,235,.2); }
input:invalid, select:invalid { border-color:#dc2626; box-shadow:0 0 0 3px rgba(220,38,38,.15); }
.actions { display:flex; gap:10px; }
.actions button { cursor:pointer; border:0; border-radius:10px; padding:10px 14px; }
.btn-primary { background:#2563eb; color:#fff; }
.btn-primary:hover { filter:brightness(.95); }
.btn-secondary { background:#f3f4f6; }
.btn-secondary:hover { filter:brightness(.97); }
table { width: 100%; border-collapse: collapse; margin-top: 12px; }
th, td { border-bottom: 1px solid #eee; padding: 10px; text-align: left; }
th { background: #fafafa; }
.toolbar { display:flex; gap:8px; align-items:center; }
.muted { color:#666; font-size:12px; }
@media (max-width: 720px) { .grid { grid-template-columns: 1fr; } }
"""

# ---------- JavaScript ----------
JS_APP = """
const tbody = document.querySelector('#carsTable tbody');
const form = document.getElementById('carForm');

const carId = document.getElementById('carId');
const brand = document.getElementById('brand');
const model = document.getElementById('model');
const year = document.getElementById('year');
const color = document.getElementById('color');
const mileage_km = document.getElementById('mileage_km');
const price = document.getElementById('price');
const quantity = document.getElementById('quantity');
const statusSel = document.getElementById('status');
const filterBrand = document.getElementById('filterBrand');

const YEAR_MIN = 1900;
const YEAR_MAX = 2100;

function onlyDigits(str) { return str.replace(/\\D+/g, ''); }
function sanitizeNumericInput(el, allowDot=false) {
  let v = el.value;
  if (allowDot) {
    v = v.replace(/[^0-9.]/g, '');
    const parts = v.split('.');
    if (parts.length > 2) v = parts[0] + '.' + parts.slice(1).join('');
    if (parts[1]) { parts[1] = parts[1].slice(0, 2); v = parts[0] + '.' + parts[1]; }
  } else {
    v = onlyDigits(v);
  }
  el.value = v;
}
function clearValidityOnInput(el){ el.addEventListener('input', ()=> el.setCustomValidity('')); }

[brand, model, year, price, mileage_km, quantity].forEach(clearValidityOnInput);

year.addEventListener('input', () => {
  sanitizeNumericInput(year, false);
  if (year.value && (Number(year.value) < YEAR_MIN || Number(year.value) > YEAR_MAX)) {
    year.setCustomValidity(`Ano deve estar entre ${YEAR_MIN} e ${YEAR_MAX}.`);
  } else year.setCustomValidity('');
});
mileage_km.addEventListener('input', () => sanitizeNumericInput(mileage_km, false));
quantity.addEventListener('input', () => sanitizeNumericInput(quantity, false));
price.addEventListener('input', () => sanitizeNumericInput(price, true));

function validateForm() {
  if (!brand.value.trim()) brand.setCustomValidity('Informe a marca.'); else brand.setCustomValidity('');
  if (!model.value.trim()) model.setCustomValidity('Informe o modelo.'); else model.setCustomValidity('');
  const y = Number(year.value);
  if (!year.value || isNaN(y) || y < YEAR_MIN || y > YEAR_MAX) year.setCustomValidity(`Ano deve estar entre ${YEAR_MIN} e ${YEAR_MAX}.`);
  else year.setCustomValidity('');
  const p = Number(price.value);
  if (!price.value || isNaN(p) || p < 0) price.setCustomValidity('Preço deve ser número >= 0 (use ponto).');
  else price.setCustomValidity('');
  const km = Number(mileage_km.value || 0);
  if (isNaN(km) || km < 0) mileage_km.setCustomValidity('KM deve ser inteiro >= 0.'); else mileage_km.setCustomValidity('');
  const q = Number(quantity.value || 0);
  if (isNaN(q) || q < 0) quantity.setCustomValidity('Quantidade deve ser inteiro >= 0.'); else quantity.setCustomValidity('');
  return form.reportValidity();
}

async function loadCars() {
  let url = '/api/cars';
  if (filterBrand.value) url += '?brand=' + encodeURIComponent(filterBrand.value.trim());
  const res = await fetch(url);
  const cars = await res.json();
  tbody.innerHTML = cars.map(c => `
    <tr>
      <td>${c.id}</td>
      <td>${c.brand}</td>
      <td>${c.model}</td>
      <td>${c.year}</td>
      <td>${c.color || '-'}</td>
      <td>${c.mileage_km ?? 0}</td>
      <td>R$ ${Number(c.price).toFixed(2)}</td>
      <td>${c.quantity}</td>
      <td>${c.status}</td>
      <td>
        <button type="button" onclick="editCar(${c.id})">Editar</button>
        <button type="button" onclick="deleteCar(${c.id})">Excluir</button>
      </td>
    </tr>
  `).join('');
}

form.addEventListener('submit', async e => {
  e.preventDefault();
  if (!validateForm()) return;
  const payload = new URLSearchParams({
    brand: brand.value.trim(),
    model: model.value.trim(),
    year: year.value,
    color: color.value.trim(),
    mileage_km: mileage_km.value || '0',
    price: price.value,
    quantity: quantity.value || '0',
    status: statusSel.value
  });
  if (carId.value) {
    await fetch('/api/cars/' + carId.value, { method:'PUT', body:payload });
  } else {
    await fetch('/api/cars', { method:'POST', body:payload });
  }
  carId.value=""; form.reset(); loadCars();
});

window.editCar = async id => {
  const res = await fetch('/api/cars');
  const cars = await res.json();
  const c = cars.find(x => x.id===id);
  if (!c) return;
  carId.value=c.id; brand.value=c.brand; model.value=c.model; year.value=c.year;
  price.value=String(Number(c.price).toFixed(2)); color.value=c.color || '';
  mileage_km.value=c.mileage_km ?? 0; quantity.value=c.quantity; statusSel.value=c.status;
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

window.deleteCar = async id => {
  if (!confirm('Confirma excluir?')) return;
  await fetch('/api/cars/' + id, { method:'DELETE' });
  loadCars();
};

document.getElementById('btnNew').onclick = ()=>{carId.value=""; form.reset();};
document.getElementById('btnFilter').onclick = loadCars;
document.getElementById('btnClear').onclick = ()=>{filterBrand.value=""; loadCars();};
loadCars();
"""

# ---------- Rotas de Front ----------
@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_PAGE

@app.get("/assets/styles.css", response_class=PlainTextResponse)
def styles():
    return PlainTextResponse(CSS_STYLES, media_type="text/css; charset=utf-8")

@app.get("/assets/app.js", response_class=PlainTextResponse)
def app_js():
    return PlainTextResponse(JS_APP, media_type="application/javascript; charset=utf-8")

# ---------- API ----------
@app.get("/api/cars")
def list_cars(brand: Optional[str] = None):
    db = SessionLocal()
    q = db.query(Car)
    if brand:
        q = q.filter(Car.brand.ilike(f"%{brand}%"))
    cars = q.order_by(Car.id.desc()).all()
    db.close()
    return [dict(
        id=c.id, brand=c.brand, model=c.model, year=c.year, color=c.color,
        mileage_km=c.mileage_km, price=float(c.price), quantity=c.quantity, status=c.status
    ) for c in cars]

@app.post("/api/cars")
def create_car(
    brand: str = Form(...), model: str = Form(...), year: int = Form(...),
    color: str = Form(""), mileage_km: int = Form(0), price: float = Form(...),
    quantity: int = Form(0), status: str = Form("Ativo"),
):
    db = SessionLocal()
    c = Car(brand=brand, model=model, year=year, color=color, mileage_km=mileage_km,
            price=price, quantity=quantity, status=status)
    db.add(c); db.commit(); db.refresh(c); db.close()
    return {"id": c.id}

@app.put("/api/cars/{car_id}")
def update_car(
    car_id: int,
    brand: str = Form(...), model: str = Form(...), year: int = Form(...),
    color: str = Form(""), mileage_km: int = Form(0), price: float = Form(...),
    quantity: int = Form(0), status: str = Form("Ativo"),
):
    db = SessionLocal()
    c = db.query(Car).get(car_id)
    if not c:
        db.close()
        raise HTTPException(404, "Car not found")
    c.brand=brand; c.model=model; c.year=year; c.color=color
    c.mileage_km=mileage_km; c.price=price; c.quantity=quantity; c.status=status
    db.commit(); db.close()
    return {"ok": True}

@app.delete("/api/cars/{car_id}")
def delete_car(car_id: int):
    db = SessionLocal()
    c = db.query(Car).get(car_id)
    if c:
        db.delete(c); db.commit()
    db.close()
    return {"ok": True}

# ---------- Main ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
