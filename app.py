# app.py — Monolito: Front (HTML + CSS + JS) + API + DB (PostgreSQL)
# Executar: python app.py
# Auto-setup:
# 1) cria o DATABASE se não existir;
# 2) cria o SCHEMA (padrão: carshop) se não existir;
# 3) cria as TABELAS (cars, clients) no schema se não existir.

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
from sqlalchemy import create_engine, Column, Integer, String, Numeric, text, UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine.url import make_url
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import Date
from datetime import datetime, date

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
ensure_schema(SCHEMA_NAME)

# ---------- Modelo CAR (com schema explícito) ----------
class Car(Base):
    __tablename__ = "cars"
    __table_args__ = {"schema": SCHEMA_NAME}  # tabela no schema carshop
    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String(60), nullable=False)
    model = Column(String(80), nullable=False)
    year = Column(Integer, nullable=False)
    color = Column(String(40), default="")
    mileage_km = Column(Integer, default=0)
    price = Column(Numeric(12, 2), nullable=False)
    quantity = Column(Integer, default=0)
    status = Column(String(12), default="Ativo")  # Ativo / Inativo

# 3) Garante tabela cars
def ensure_cars_table():
    insp = sa_inspect(engine)
    if not insp.has_table("cars", schema=SCHEMA_NAME):
        print(f"[SETUP] Criando tabela {SCHEMA_NAME}.cars ...")
        Base.metadata.create_all(bind=engine, tables=[Car.__table__])
    else:
        # sincroniza metadados sem recriar
        Base.metadata.create_all(bind=engine, tables=[Car.__table__])
        print(f"[INFO] Tabela {SCHEMA_NAME}.cars já existe — nenhuma ação necessária.")
ensure_cars_table()

# ---------- Modelo CLIENTE (seguindo padrão do Car) ----------
class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (
        UniqueConstraint("cpf", name="uq_clients_cpf"),
        {"schema": SCHEMA_NAME},
    )
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    cpf = Column(String(11), nullable=False, index=True)  # somente dígitos (11)
    data_nascimento = Column(Date, nullable=False)

# 4) Garante tabela clients
def ensure_clients_table():
    insp = sa_inspect(engine)
    if not insp.has_table("clients", schema=SCHEMA_NAME):
        print(f"[SETUP] Criando tabela {SCHEMA_NAME}.clients ...")
        Base.metadata.create_all(bind=engine, tables=[Client.__table__])
    else:
        Base.metadata.create_all(bind=engine, tables=[Client.__table__])
        print(f"[INFO] Tabela {SCHEMA_NAME}.clients já existe — nenhuma ação necessária.")
ensure_clients_table()

# ---------- App ----------
app = FastAPI(title="CarShop • Impacta (PostgreSQL, auto-setup com schema)")

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
input, select, button, a.btn { padding:10px 12px; border:1px solid #d9d9d9; border-radius:8px; background:#fff; text-decoration:none; display:inline-block; }
input:focus, select:focus { outline: none; border-color:#2563eb; box-shadow:0 0 0 3px rgba(37,99,235,.2); }
input:invalid, select:invalid { border-color:#dc2626; box-shadow:0 0 0 3px rgba(220,38,38,.15); }
.actions { display:flex; gap:10px; flex-wrap:wrap; }
.actions .btn, button { cursor:pointer; border:0; border-radius:10px; padding:10px 14px; }
.btn-primary { background:#2563eb; color:#fff; }
.btn-primary:hover { filter:brightness(.95); }
.btn-secondary { background:#f3f4f6; }
.btn-secondary:hover { filter:brightness(.97); }
.btn-ghost { background:#ffffff; border:1px solid #e5e5e5; }
.btn-ghost:hover { filter:brightness(.98); }
table { width: 100%; border-collapse: collapse; margin-top: 12px; }
th, td { border-bottom: 1px solid #eee; padding: 10px; text-align: left; }
th { background: #fafafa; }
.toolbar { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.muted { color:#666; font-size:12px; }

.nav { display:flex; gap:10px; margin-bottom:16px; flex-wrap:wrap; }
.nav a { border:1px solid #e5e5e5; padding:8px 12px; border-radius:8px; }
.nav a.active { background:#2563eb; color:#fff; border-color:#2563eb; }
.cards { display:grid; grid-template-columns: repeat(auto-fill,minmax(220px,1fr)); gap:16px; }
.card.center { text-align:center; }
.card .big { font-size:18px; font-weight:600; }
.card .desc { color:#555; margin:6px 0 12px; min-height: 36px; }
@media (max-width: 720px) { .grid { grid-template-columns: 1fr; } }
"""

# ---------- HTML Dashboard ----------
DASHBOARD_PAGE = """<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <title>CarShop • Dashboard</title>
  <link rel="stylesheet" href="/assets/styles.css">
  <meta name="viewport" content="width=device-width, initial-scale=1" />
</head>
<body>
  <div class="container">
    <h1>CarShop • Dashboard</h1>
    <div class="nav">
      <a href="/" class="active">Início</a>
      <a href="/cars">Carros</a>
      <a href="/clients">Clientes</a>
      <a href="/sales">Vendas</a>
      <a href="/sellers">Vendedores</a>
    </div>

    <div class="cards">
      <div class="card center">
        <div class="big">Carros</div>
        <div class="desc">Cadastro e catálogo de veículos.</div>
        <a class="btn btn-primary" href="/cars">Abrir</a>
      </div>

      <div class="card center">
        <div class="big">Clientes</div>
        <div class="desc">Cadastro simples com nome, CPF e data de nascimento.</div>
        <a class="btn btn-primary" href="/clients">Abrir</a>
      </div>

      <div class="card center">
        <div class="big">Vendas</div>
        <div class="desc">Fluxo de vendas (em breve). Já com botões de atalho.</div>
        <a class="btn btn-secondary" href="/sales">Abrir</a>
      </div>

      <div class="card center">
        <div class="big">Vendedores</div>
        <div class="desc">Cadastro de vendedores (em breve).</div>
        <a class="btn btn-secondary" href="/sellers">Abrir</a>
      </div>
    </div>
  </div>
</body>
</html>
"""

# ---------- HTML Carros ----------
HTML_CARS = """<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <title>CarShop • Carros</title>
  <link rel="stylesheet" href="/assets/styles.css">
  <meta name="viewport" content="width=device-width, initial-scale=1" />
</head>
<body>
  <div class="container">
    <h1>Carros</h1>
    <div class="nav">
      <a href="/">Início</a>
      <a href="/cars" class="active">Carros</a>
      <a href="/clients">Clientes</a>
      <a href="/sales">Vendas</a>
      <a href="/sellers">Vendedores</a>
    </div>

    <h2>Cadastro / Edição</h2>
    <form id="carForm" class="card">
      <input type="hidden" id="carId">
      <div class="grid">
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

# ---------- HTML Clientes ----------
CLIENTS_PAGE = """<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <title>Clientes • CarShop</title>
  <link rel="stylesheet" href="/assets/styles.css">
  <meta name="viewport" content="width=device-width, initial-scale=1" />
</head>
<body>
  <div class="container">
    <h1>Clientes</h1>
    <div class="nav">
      <a href="/">Início</a>
      <a href="/cars">Carros</a>
      <a href="/clients" class="active">Clientes</a>
      <a href="/sales">Vendas</a>
      <a href="/sellers">Vendedores</a>
    </div>

    <h2>Cadastro / Edição</h2>
    <form id="clientForm" class="card">
      <input type="hidden" id="clientId">
      <div class="grid">
        <div class="field">
          <label for="nome">Nome</label>
          <input id="nome" required placeholder="Ex.: Maria Silva">
        </div>
        <div class="field">
          <label for="cpf">CPF</label>
          <input id="cpf" required placeholder="Somente dígitos (11)">
        </div>
        <div class="field">
          <label for="data_nascimento">Data de Nascimento</label>
          <input id="data_nascimento" type="date" required>
        </div>

        <div class="actions" style="grid-column: 1 / -1; margin-top: 4px;">
          <button type="submit" class="btn-primary">Salvar</button>
          <button type="button" id="btnNewClient" class="btn-secondary">Novo</button>
        </div>
      </div>
    </form>

    <h2>Lista</h2>
    <div class="card">
      <div class="toolbar" style="margin-bottom:10px;">
        <input id="filterNome" placeholder="Filtrar por nome" style="flex:1;">
        <input id="filterCPF" placeholder="Filtrar por CPF (somente dígitos)" style="flex:1;">
        <button id="btnFilterClient" class="btn-secondary">Filtrar</button>
        <button id="btnClearClient" class="btn-secondary">Limpar</button>
      </div>

      <table id="clientsTable">
        <thead>
          <tr>
            <th>ID</th><th>Nome</th><th>CPF</th><th>Nascimento</th><th>Ações</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>

    <p class="muted" style="margin-top:12px;">
      Dica: CPF é salvo apenas com dígitos (11). Unicidade garantida.
    </p>
  </div>

  <script src="/assets/clients.js"></script>
</body>
</html>
"""

# ---------- HTML Vendas (placeholder preparado) ----------
SALES_PAGE = """<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <title>Vendas • CarShop</title>
  <link rel="stylesheet" href="/assets/styles.css">
  <meta name="viewport" content="width=device-width, initial-scale=1" />
</head>
<body>
  <div class="container">
    <h1>Vendas</h1>
    <div class="nav">
      <a href="/">Início</a>
      <a href="/cars">Carros</a>
      <a href="/clients">Clientes</a>
      <a href="/sales" class="active">Vendas</a>
      <a href="/sellers">Vendedores</a>
    </div>

    <div class="card">
      <p class="muted">Em breve: fluxo completo de vendas.</p>
      <div class="actions">
        <a class="btn btn-primary" href="/clients">+ Nova Venda (selecionar Cliente)</a>
        <a class="btn btn-secondary" href="/cars">Escolher Carro</a>
      </div>
    </div>
  </div>
</body>
</html>
"""

# ---------- HTML Vendedores (placeholder preparado) ----------
SELLERS_PAGE = """<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <title>Vendedores • CarShop</title>
  <link rel="stylesheet" href="/assets/styles.css">
  <meta name="viewport" content="width=device-width, initial-scale=1" />
</head>
<body>
  <div class="container">
    <h1>Vendedores</h1>
    <div class="nav">
      <a href="/">Início</a>
      <a href="/cars">Carros</a>
      <a href="/clients">Clientes</a>
      <a href="/sales">Vendas</a>
      <a href="/sellers" class="active">Vendedores</a>
    </div>

    <div class="card">
      <p class="muted">Em breve: cadastro de vendedores.</p>
      <div class="actions">
        <a class="btn btn-primary" href="/sellers">+ Cadastrar Vendedor</a>
      </div>
    </div>
  </div>
</body>
</html>
"""

# ---------- JavaScript Carros ----------
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
  if (filterBrand && filterBrand.value) url += '?brand=' + encodeURIComponent(filterBrand.value.trim());
  const res = await fetch(url);
  const cars = await res.json();
  const rows = cars.map(c => `
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
  const tbody = document.querySelector('#carsTable tbody');
  if (tbody) tbody.innerHTML = rows;
}

if (form) {
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
}

window.editCar = async id => {
  const res = await fetch('/api/cars');
  const cars = await res.json();
  const c = cars.find(x => x.id===id);
  if (!c) return;
  document.getElementById('carId').value=c.id;
  document.getElementById('brand').value=c.brand;
  document.getElementById('model').value=c.model;
  document.getElementById('year').value=c.year;
  document.getElementById('price').value=String(Number(c.price).toFixed(2));
  document.getElementById('color').value=c.color || '';
  document.getElementById('mileage_km').value=c.mileage_km ?? 0;
  document.getElementById('quantity').value=c.quantity;
  document.getElementById('status').value=c.status;
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

window.deleteCar = async id => {
  if (!confirm('Confirma excluir?')) return;
  await fetch('/api/cars/' + id, { method:'DELETE' });
  loadCars();
};

if (document.getElementById('btnNew')) {
  document.getElementById('btnNew').onclick = ()=>{document.getElementById('carId').value=""; form.reset();};
}
if (document.getElementById('btnFilter')) {
  document.getElementById('btnFilter').onclick = loadCars;
}
if (document.getElementById('btnClear')) {
  document.getElementById('btnClear').onclick = ()=>{document.getElementById('filterBrand').value=""; loadCars();};
}
if (document.getElementById('carsTable')) loadCars();
"""

# ---------- JavaScript Clientes ----------
JS_CLIENTS = r"""
const tbodyC = document.querySelector('#clientsTable tbody');
const formC = document.getElementById('clientForm');

const clientId = document.getElementById('clientId');
const nome = document.getElementById('nome');
const cpf = document.getElementById('cpf');
const data_nascimento = document.getElementById('data_nascimento');

const filterNome = document.getElementById('filterNome');
const filterCPF = document.getElementById('filterCPF');

function onlyDigits(str){ return (str || '').replace(/\D+/g, ''); }

if (cpf) {
  cpf.addEventListener('input', ()=> {
    cpf.value = onlyDigits(cpf.value).slice(0,11);
    if (cpf.value.length !== 11) cpf.setCustomValidity('CPF deve conter 11 dígitos.');
    else cpf.setCustomValidity('');
  });
}

function validateClientForm(){
  if (!nome.value.trim()) { nome.setCustomValidity('Informe o nome.'); }
  else nome.setCustomValidity('');
  const c = onlyDigits(cpf.value);
  if (c.length !== 11) cpf.setCustomValidity('CPF deve conter 11 dígitos.');
  else cpf.setCustomValidity('');
  if (!data_nascimento.value) data_nascimento.setCustomValidity('Informe a data.');
  else data_nascimento.setCustomValidity('');
  return formC.reportValidity();
}

async function loadClients(){
  const params = new URLSearchParams();
  if (filterNome && filterNome.value.trim()) params.set('nome', filterNome.value.trim());
  if (filterCPF && onlyDigits(filterCPF.value)) params.set('cpf', onlyDigits(filterCPF.value));
  const qs = params.toString() ? ('?' + params.toString()) : '';
  const res = await fetch('/api/clients' + qs);
  const list = await res.json();
  if (!tbodyC) return;
  tbodyC.innerHTML = list.map(c => `
    <tr>
      <td>${c.id}</td>
      <td>${c.nome}</td>
      <td>${formatCPF(c.cpf)}</td>
      <td>${c.data_nascimento}</td>
      <td>
        <button type="button" onclick="editClient(${c.id})">Editar</button>
        <button type="button" onclick="deleteClient(${c.id})">Excluir</button>
      </td>
    </tr>
  `).join('');
}

function formatCPF(v){
  const d = onlyDigits(v);
  if (d.length !== 11) return v || '';
  return `${d.slice(0,3)}.${d.slice(3,6)}.${d.slice(6,9)}-${d.slice(9)}`;
}

if (formC) {
  formC.addEventListener('submit', async e => {
    e.preventDefault();
    if (!validateClientForm()) return;
    const payload = new URLSearchParams({
      nome: nome.value.trim(),
      cpf: onlyDigits(cpf.value),
      data_nascimento: data_nascimento.value
    });
    if (clientId.value){
      await fetch('/api/clients/' + clientId.value, { method:'PUT', body: payload });
    } else {
      await fetch('/api/clients', { method:'POST', body: payload });
    }
    clientId.value = ""; formC.reset(); loadClients();
  });
}

window.editClient = async id => {
  const res = await fetch('/api/clients');
  const list = await res.json();
  const c = list.find(x => x.id === id);
  if (!c) return;
  clientId.value = c.id;
  nome.value = c.nome;
  cpf.value = c.cpf;
  data_nascimento.value = c.data_nascimento;
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

window.deleteClient = async id => {
  if (!confirm('Confirma excluir?')) return;
  await fetch('/api/clients/' + id, { method:'DELETE' });
  loadClients();
};

if (document.getElementById('btnNewClient')) {
  document.getElementById('btnNewClient').onclick = ()=>{ clientId.value=""; formC.reset(); };
}
if (document.getElementById('btnFilterClient')) {
  document.getElementById('btnFilterClient').onclick = loadClients;
}
if (document.getElementById('btnClearClient')) {
  document.getElementById('btnClearClient').onclick = ()=>{ filterNome.value=""; filterCPF.value=""; loadClients(); };
}

if (tbodyC) loadClients();
"""

# ---------- Rotas de Front ----------
@app.get("/", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_PAGE

@app.get("/cars", response_class=HTMLResponse)
def cars_page():
    return HTML_CARS

@app.get("/clients", response_class=HTMLResponse)
def clients_page():
    return CLIENTS_PAGE

@app.get("/sales", response_class=HTMLResponse)
def sales_page():
    return SALES_PAGE

@app.get("/sellers", response_class=HTMLResponse)
def sellers_page():
    return SELLERS_PAGE

@app.get("/assets/styles.css", response_class=PlainTextResponse)
def styles():
    return PlainTextResponse(CSS_STYLES, media_type="text/css; charset=utf-8")

@app.get("/assets/app.js", response_class=PlainTextResponse)
def app_js():
    return PlainTextResponse(JS_APP, media_type="application/javascript; charset=utf-8")

@app.get("/assets/clients.js", response_class=PlainTextResponse)
def clients_js():
    return PlainTextResponse(JS_CLIENTS, media_type="application/javascript; charset=utf-8")

# ---------- API: Cars ----------
@app.get("/api/cars")
def list_cars(brand: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(Car)
        if brand:
            q = q.filter(Car.brand.ilike(f"%{brand}%"))
        cars = q.order_by(Car.id.desc()).all()
        return [dict(
            id=c.id, brand=c.brand, model=c.model, year=c.year, color=c.color,
            mileage_km=c.mileage_km, price=float(c.price), quantity=c.quantity, status=c.status
        ) for c in cars]
    finally:
        db.close()

@app.post("/api/cars")
def create_car(
    brand: str = Form(...), model: str = Form(...), year: int = Form(...),
    color: str = Form(""), mileage_km: int = Form(0), price: float = Form(...),
    quantity: int = Form(0), status: str = Form("Ativo"),
):
    db = SessionLocal()
    try:
        c = Car(brand=brand, model=model, year=year, color=color, mileage_km=mileage_km,
                price=price, quantity=quantity, status=status)
        db.add(c); db.commit(); db.refresh(c)
        return {"id": c.id}
    finally:
        db.close()

@app.put("/api/cars/{car_id}")
def update_car(
    car_id: int,
    brand: str = Form(...), model: str = Form(...), year: int = Form(...),
    color: str = Form(""), mileage_km: int = Form(0), price: float = Form(...),
    quantity: int = Form(0), status: str = Form("Ativo"),
):
    db = SessionLocal()
    try:
        c = db.query(Car).get(car_id)
        if not c:
            raise HTTPException(404, "Car not found")
        c.brand=brand; c.model=model; c.year=year; c.color=color
        c.mileage_km=mileage_km; c.price=price; c.quantity=quantity; c.status=status
        db.commit()
        return {"ok": True}
    finally:
        db.close()

@app.delete("/api/cars/{car_id}")
def delete_car(car_id: int):
    db = SessionLocal()
    try:
        c = db.query(Car).get(car_id)
        if c:
            db.delete(c); db.commit()
        return {"ok": True}
    finally:
        db.close()

# ---------- Helpers Clientes ----------
def _parse_date_or_400(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail="data_nascimento inválida (use YYYY-MM-DD)")

def _cpf_digits_or_400(value: str) -> str:
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    if len(digits) != 11:
        raise HTTPException(status_code=400, detail="CPF deve conter 11 dígitos.")
    return digits

# ---------- API: Clients ----------
@app.get("/api/clients")
def list_clients(nome: Optional[str] = None, cpf: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(Client)
        if nome:
            q = q.filter(Client.nome.ilike(f"%{nome}%"))
        if cpf:
            digits = "".join(ch for ch in cpf if ch.isdigit())
            if digits:
                q = q.filter(Client.cpf == digits)
        rows = q.order_by(Client.id.desc()).all()
        return [
            dict(
                id=r.id,
                nome=r.nome,
                cpf=r.cpf,
                data_nascimento=r.data_nascimento.isoformat(),
            )
            for r in rows
        ]
    finally:
        db.close()

@app.post("/api/clients")
def create_client(
    nome: str = Form(...),
    cpf: str = Form(...),
    data_nascimento: str = Form(...),
):
    db = SessionLocal()
    try:
        cpf_digits = _cpf_digits_or_400(cpf)
        dn = _parse_date_or_400(data_nascimento)

        exists = db.query(Client).filter(Client.cpf == cpf_digits).first()
        if exists:
            raise HTTPException(status_code=409, detail="CPF já cadastrado.")

        c = Client(nome=nome.strip(), cpf=cpf_digits, data_nascimento=dn)
        db.add(c); db.commit(); db.refresh(c)
        return {"id": c.id}
    finally:
        db.close()

@app.put("/api/clients/{client_id}")
def update_client(
    client_id: int,
    nome: str = Form(...),
    cpf: str = Form(...),
    data_nascimento: str = Form(...),
):
    db = SessionLocal()
    try:
        c = db.query(Client).get(client_id)
        if not c:
            raise HTTPException(status_code=404, detail="Cliente não encontrado.")

        cpf_digits = _cpf_digits_or_400(cpf)
        dn = _parse_date_or_400(data_nascimento)

        dup = db.query(Client).filter(Client.cpf == cpf_digits, Client.id != client_id).first()
        if dup:
            raise HTTPException(status_code=409, detail="CPF já cadastrado em outro cliente.")

        c.nome = nome.strip()
        c.cpf = cpf_digits
        c.data_nascimento = dn

        db.commit()
        return {"ok": True}
    finally:
        db.close()

@app.delete("/api/clients/{client_id}")
def delete_client(client_id: int):
    db = SessionLocal()
    try:
        c = db.query(Client).get(client_id)
        if c:
            db.delete(c); db.commit()
        return {"ok": True}
    finally:
        db.close()

# ---------- Main ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
