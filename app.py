# app.py — Monolito: Front (HTML + CSS + JS) + API + DB (PostgreSQL, sem SQLAlchemy)
# Executar: python app.py
# Auto-setup:
# 1) cria o DATABASE se não existir;
# 2) cria o SCHEMA (padrão: carshop) se não existir;
# 3) cria as TABELAS (cars, clients, sellers, orders) no schema se não existir.

import subprocess, sys, os
from typing import Optional
from urllib.parse import urlparse
from datetime import datetime, date

# ---------- Auto-instalação de dependências ----------
REQUIRED = [
    "fastapi",
    "uvicorn[standard]",
    "pydantic",
    "psycopg2-binary",   # PostgreSQL driver
    "python-multipart",  # necessário para Form(...)
]
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
import psycopg2

# ---------- Config do banco (PostgreSQL) ----------
# Mantém o mesmo formato do monolito original: postgresql+psycopg2://user:pass@host:port/db
DEFAULT_PG_URL = "postgresql+psycopg2://postgres@localhost:5432/carshop"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_PG_URL)

if DATABASE_URL.startswith("sqlite"):
    raise RuntimeError("SQLite não é permitido. Use PostgreSQL (DATABASE_URL postgresql+psycopg2://...).")

# Nome do schema (padrão 'carshop'); pode trocar via variável de ambiente DB_SCHEMA
SCHEMA_NAME = os.getenv("DB_SCHEMA", "carshop")

def parse_pg_url(url: str) -> dict:
    """
    Converte a URL no formato postgresql+psycopg2://user:pass@host:port/db
    em um dicionário para psycopg2.connect.
    """
    parsed = urlparse(url)
    # esquema pode vir como "postgresql+psycopg2"
    user = parsed.username or "postgres"
    password = parsed.password or ""
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    dbname = (parsed.path or "/").lstrip("/") or "postgres"
    return dict(user=user, password=password, host=host, port=port, dbname=dbname)

PG_CONFIG = parse_pg_url(DATABASE_URL)

def get_conn(dbname: Optional[str] = None):
    cfg = PG_CONFIG.copy()
    if dbname:
        cfg["dbname"] = dbname
    return psycopg2.connect(**cfg)

def ensure_database():
    """
    Cria o database alvo se não existir, conectando-se ao DB 'postgres'.
    """
    target_db = PG_CONFIG["dbname"]
    admin_conn = get_conn(dbname="postgres")
    admin_conn.autocommit = True
    try:
        with admin_conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
            exists = cur.fetchone()
            if not exists:
                print(f"[SETUP] Criando database '{target_db}' ...")
                cur.execute(f'CREATE DATABASE "{target_db}"')
    finally:
        admin_conn.close()

# 1) Garante database
ensure_database()

def ensure_schema(schema: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        conn.commit()
    finally:
        conn.close()

# 2) Garante schema
ensure_schema(SCHEMA_NAME)

def ensure_tables(schema: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Tabela cars
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS "{schema}".cars (
                id SERIAL PRIMARY KEY,
                brand        VARCHAR(60)  NOT NULL,
                model        VARCHAR(80)  NOT NULL,
                year         INTEGER      NOT NULL,
                color        VARCHAR(40)  DEFAULT '',
                mileage_km   INTEGER      DEFAULT 0,
                price        NUMERIC(12,2) NOT NULL,
                quantity     INTEGER      DEFAULT 0,
                status       VARCHAR(12)  DEFAULT 'Ativo'
            );
            """)

            # Tabela clients
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS "{schema}".clients (
                id              SERIAL PRIMARY KEY,
                nome            VARCHAR(200) NOT NULL,
                cpf             VARCHAR(11)  NOT NULL UNIQUE,
                data_nascimento DATE         NOT NULL
            );
            """)

            # Tabela sellers
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS "{schema}".sellers (
                id      SERIAL PRIMARY KEY,
                nome    VARCHAR(200) NOT NULL,
                email   VARCHAR(200) NOT NULL,
                cpf     VARCHAR(11)  NOT NULL UNIQUE
            );
            """)

            # Tabela orders (pedidos)
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS "{schema}".orders (
                id          SERIAL PRIMARY KEY,
                seller_id   INTEGER     NOT NULL,
                client_id   INTEGER     NOT NULL,
                car_id      INTEGER     NOT NULL,
                quantity    INTEGER     NOT NULL,
                total_value NUMERIC(12,2) NOT NULL,
                created_at  TIMESTAMP   DEFAULT NOW()
            );
            """)
        conn.commit()
        print(f"[SETUP] Tabelas garantidas em schema '{schema}'.")
    finally:
        conn.close()

# 3) Garante tabelas
ensure_tables(SCHEMA_NAME)

# ---------- App ----------
app = FastAPI(title="CarShop • Impacta (PostgreSQL, auto-setup com schema, sem SQLAlchemy)")

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
        <div class="desc">Fluxo de pedidos com baixa automática de estoque.</div>
        <a class="btn btn-primary" href="/sales">Abrir</a>
      </div>

      <div class="card center">
        <div class="big">Vendedores</div>
        <div class="desc">Cadastro de vendedores com nome, e-mail e CPF.</div>
        <a class="btn btn-primary" href="/sellers">Abrir</a>
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

        <div class="actions" style="grid-column: 1 / -1; margin-top: 4px%;">
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

# ---------- HTML Vendas (Registrar Pedido) ----------
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
    <h1>Vendas / Pedidos</h1>
    <div class="nav">
      <a href="/">Início</a>
      <a href="/cars">Carros</a>
      <a href="/clients">Clientes</a>
      <a href="/sales" class="active">Vendas</a>
      <a href="/sellers">Vendedores</a>
    </div>

    <h2>Registrar Pedido</h2>
    <form id="orderForm" class="card">
      <div class="grid">
        <div class="field">
          <label for="orderSeller">Vendedor</label>
          <select id="orderSeller" required>
            <option value="">Selecione...</option>
          </select>
        </div>

        <div class="field">
          <label for="orderClient">Cliente</label>
          <select id="orderClient" required>
            <option value="">Selecione...</option>
          </select>
        </div>

        <div class="field">
          <label for="orderCar">Carro</label>
          <select id="orderCar" required>
            <option value="">Selecione...</option>
          </select>
        </div>

        <div class="field">
          <label for="orderQuantity">Quantidade</label>
          <input type="number" id="orderQuantity" min="1" value="1" required>
        </div>

        <div class="field">
          <label for="orderTotal">Valor total (R$)</label>
          <input id="orderTotal" type="text" readonly placeholder="Será calculado">
        </div>

        <div class="actions" style="grid-column: 1 / -1; margin-top: 4px;">
          <button type="submit" class="btn-primary">Registrar Pedido</button>
        </div>
      </div>
    </form>

    <h2>Histórico de Pedidos</h2>
    <div class="card">
      <table id="ordersTable">
        <thead>
          <tr>
            <th>ID Pedido</th>
            <th>ID Carro</th>
            <th>Carro</th>
            <th>Valor Unit. (R$)</th>
            <th>Qtd</th>
            <th>Total (R$)</th>
            <th>ID Vendedor</th>
            <th>Vendedor</th>
            <th>ID Cliente</th>
            <th>Cliente</th>
            <th>Data</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>

    <p class="muted" style="margin-top:12px;">
      Registre pedidos utilizando os cadastros existentes de clientes, carros e vendedores.
    </p>
  </div>

  <script src="/assets/sales.js"></script>
</body>
</html>
"""

# ---------- HTML Vendedores (CRUD completo) ----------
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

    <h2>Cadastro / Edição</h2>
    <form id="sellerForm" class="card">
      <input type="hidden" id="sellerId">
      <div class="grid">
        <div class="field">
          <label for="sellerNome">Nome</label>
          <input id="sellerNome" required placeholder="Ex.: João Vendedor">
        </div>
        <div class="field">
          <label for="sellerEmail">E-mail</label>
          <input id="sellerEmail" required placeholder="Ex.: joao@carshop.com">
        </div>
        <div class="field">
          <label for="sellerCPF">CPF</label>
          <input id="sellerCPF" required placeholder="Somente dígitos (11)">
        </div>

        <div class="actions" style="grid-column: 1 / -1; margin-top: 4px;">
          <button type="submit" class="btn-primary">Salvar</button>
          <button type="button" id="btnNewSeller" class="btn-secondary">Novo</button>
        </div>
      </div>
    </form>

    <h2>Lista</h2>
    <div class="card">
      <div class="toolbar" style="margin-bottom:10px;">
        <input id="filterSellerNome" placeholder="Filtrar por nome" style="flex:1;">
        <input id="filterSellerEmail" placeholder="Filtrar por e-mail" style="flex:1;">
        <input id="filterSellerCPF" placeholder="Filtrar por CPF (somente dígitos)" style="flex:1;">
        <button id="btnFilterSeller" class="btn-secondary">Filtrar</button>
        <button id="btnClearSeller" class="btn-secondary">Limpar</button>
      </div>

      <table id="sellersTable">
        <thead>
          <tr>
            <th>ID</th><th>Nome</th><th>E-mail</th><th>CPF</th><th>Ações</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>

    <p class="muted" style="margin-top:12px;">
      CPF é salvo apenas com dígitos (11). Unicidade garantida por CPF.
    </p>
  </div>

  <script src="/assets/sellers.js"></script>
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

# ---------- JavaScript Vendedores ----------
JS_SELLERS = r"""
const tbodyS = document.querySelector('#sellersTable tbody');
const formS = document.getElementById('sellerForm');

const sellerId = document.getElementById('sellerId');
const sellerNome = document.getElementById('sellerNome');
const sellerEmail = document.getElementById('sellerEmail');
const sellerCPF = document.getElementById('sellerCPF');

const filterSellerNome = document.getElementById('filterSellerNome');
const filterSellerEmail = document.getElementById('filterSellerEmail');
const filterSellerCPF = document.getElementById('filterSellerCPF');

function onlyDigits(str){ return (str || '').replace(/\D+/g, ''); }

if (sellerCPF) {
  sellerCPF.addEventListener('input', ()=> {
    sellerCPF.value = onlyDigits(sellerCPF.value).slice(0,11);
    if (sellerCPF.value.length !== 11) sellerCPF.setCustomValidity('CPF deve conter 11 dígitos.');
    else sellerCPF.setCustomValidity('');
  });
}

if (sellerEmail) {
  sellerEmail.addEventListener('input', ()=> {
    const v = (sellerEmail.value || '').trim();
    if (!v.includes('@') || !v.includes('.')) {
      sellerEmail.setCustomValidity('Informe um e-mail válido.');
    } else {
      sellerEmail.setCustomValidity('');
    }
  });
}

function validateSellerForm(){
  if (!sellerNome.value.trim()) { sellerNome.setCustomValidity('Informe o nome.'); }
  else sellerNome.setCustomValidity('');
  const c = onlyDigits(sellerCPF.value);
  if (c.length !== 11) sellerCPF.setCustomValidity('CPF deve conter 11 dígitos.');
  else sellerCPF.setCustomValidity('');
  const v = (sellerEmail.value || '').trim();
  if (!v.includes('@') || !v.includes('.')) {
    sellerEmail.setCustomValidity('Informe um e-mail válido.');
  } else {
    sellerEmail.setCustomValidity('');
  }
  return formS.reportValidity();
}

function formatCPF(v){
  const d = onlyDigits(v);
  if (d.length !== 11) return v || '';
  return `${d.slice(0,3)}.${d.slice(3,6)}.${d.slice(6,9)}-${d.slice(9)}`;
}

async function loadSellers(){
  const params = new URLSearchParams();
  if (filterSellerNome && filterSellerNome.value.trim()) params.set('nome', filterSellerNome.value.trim());
  if (filterSellerEmail && filterSellerEmail.value.trim()) params.set('email', filterSellerEmail.value.trim());
  if (filterSellerCPF && onlyDigits(filterSellerCPF.value)) params.set('cpf', onlyDigits(filterSellerCPF.value));
  const qs = params.toString() ? ('?' + params.toString()) : '';
  const res = await fetch('/api/sellers' + qs);
  const list = await res.json();
  if (!tbodyS) return;
  tbodyS.innerHTML = list.map(s => `
    <tr>
      <td>${s.id}</td>
      <td>${s.nome}</td>
      <td>${s.email}</td>
      <td>${formatCPF(s.cpf)}</td>
      <td>
        <button type="button" onclick="editSeller(${s.id})">Editar</button>
        <button type="button" onclick="deleteSeller(${s.id})">Excluir</button>
      </td>
    </tr>
  `).join('');
}

if (formS) {
  formS.addEventListener('submit', async e => {
    e.preventDefault();
    if (!validateSellerForm()) return;
    const payload = new URLSearchParams({
      nome: sellerNome.value.trim(),
      email: sellerEmail.value.trim(),
      cpf: onlyDigits(sellerCPF.value)
    });
    if (sellerId.value){
      await fetch('/api/sellers/' + sellerId.value, { method:'PUT', body: payload });
    } else {
      await fetch('/api/sellers', { method:'POST', body: payload });
    }
    sellerId.value = ""; formS.reset(); loadSellers();
  });
}

window.editSeller = async id => {
  const res = await fetch('/api/sellers');
  const list = await res.json();
  const s = list.find(x => x.id === id);
  if (!s) return;
  sellerId.value = s.id;
  sellerNome.value = s.nome;
  sellerEmail.value = s.email;
  sellerCPF.value = s.cpf;
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

window.deleteSeller = async id => {
  if (!confirm('Confirma excluir?')) return;
  await fetch('/api/sellers/' + id, { method:'DELETE' });
  loadSellers();
};

if (document.getElementById('btnNewSeller')) {
  document.getElementById('btnNewSeller').onclick = ()=>{ sellerId.value=""; formS.reset(); };
}
if (document.getElementById('btnFilterSeller')) {
  document.getElementById('btnFilterSeller').onclick = loadSellers;
}
if (document.getElementById('btnClearSeller')) {
  document.getElementById('btnClearSeller').onclick = ()=>{ 
    filterSellerNome.value=""; 
    filterSellerEmail.value="";
    filterSellerCPF.value=""; 
    loadSellers(); 
  };
}

if (tbodyS) loadSellers();
"""

# ---------- JavaScript Vendas / Pedidos ----------
JS_SALES = r"""
const orderForm = document.getElementById('orderForm');

const sellerSelect = document.getElementById('orderSeller');
const clientSelect = document.getElementById('orderClient');
const carSelect = document.getElementById('orderCar');
const quantityInput = document.getElementById('orderQuantity');
const totalInput = document.getElementById('orderTotal');
const ordersTbody = document.querySelector('#ordersTable tbody');

let carsCache = [];

function formatMoney(v) {
  const n = Number(v || 0);
  return n.toFixed(2);
}

async function loadSellers() {
  if (!sellerSelect) return;
  const res = await fetch('/api/sellers');
  const list = await res.json();
  sellerSelect.innerHTML = '<option value=\"\">Selecione...</option>' +
    list.map(s => `<option value=\"${s.id}\">${s.nome}</option>`).join('');
}

async function loadClients() {
  if (!clientSelect) return;
  const res = await fetch('/api/clients');
  const list = await res.json();
  clientSelect.innerHTML = '<option value=\"\">Selecione...</option>' +
    list.map(c => `<option value=\"${c.id}\">${c.nome}</option>`).join('');
}

async function loadCarsForOrder() {
  if (!carSelect) return;
  const res = await fetch('/api/cars');
  const list = await res.json();
  // Só carros ativos com estoque > 0
  carsCache = list.filter(c => c.status === 'Ativo' && (c.quantity || 0) > 0);

  carSelect.innerHTML = '<option value=\"\">Selecione...</option>' +
    carsCache.map(c =>
      `<option value=\"${c.id}\">${c.brand} ${c.model} (Estoque: ${c.quantity} • R$ ${formatMoney(c.price)})</option>`
    ).join('');
  updateTotal();
}

function updateTotal() {
  if (!carSelect || !totalInput || !quantityInput) return;
  const carId = parseInt(carSelect.value || '0', 10);
  const qty = parseInt(quantityInput.value || '0', 10);
  const car = carsCache.find(c => c.id === carId);
  if (!car || !qty || qty <= 0) {
    totalInput.value = '';
    return;
  }
  const total = Number(car.price) * qty;
  totalInput.value = formatMoney(total);
}

async function loadOrders() {
  if (!ordersTbody) return;
  const res = await fetch('/api/orders');
  const list = await res.json();
  ordersTbody.innerHTML = list.map(o => `
    <tr>
      <td>${o.id}</td>
      <td>${o.car_id}</td>
      <td>${o.car_description}</td>
      <td>R$ ${formatMoney(o.car_price)}</td>
      <td>${o.quantity}</td>
      <td>R$ ${formatMoney(o.total_value)}</td>
      <td>${o.seller_id}</td>
      <td>${o.seller}</td>
      <td>${o.client_id}</td>
      <td>${o.client}</td>
      <td>${o.created_at || ''}</td>
    </tr>
  `).join('');
}

if (orderForm) {
  carSelect.addEventListener('change', updateTotal);
  quantityInput.addEventListener('input', () => {
    if (!quantityInput.value || Number(quantityInput.value) < 1) {
      quantityInput.value = 1;
    }
    updateTotal();
  });

  orderForm.addEventListener('submit', async e => {
    e.preventDefault();
    if (!sellerSelect.value || !clientSelect.value || !carSelect.value) {
      alert('Selecione vendedor, cliente e carro.');
      return;
    }
    const qty = parseInt(quantityInput.value || '0', 10);
    if (!qty || qty <= 0) {
      alert('Quantidade deve ser pelo menos 1.');
      return;
    }
    const payload = new URLSearchParams({
      seller_id: sellerSelect.value,
      client_id: clientSelect.value,
      car_id: carSelect.value,
      quantity: String(qty),
    });

    const res = await fetch('/api/orders', {
      method: 'POST',
      body: payload
    });

    if (!res.ok) {
      let msg = 'Erro ao registrar pedido.';
      try {
        const err = await res.json();
        if (err && err.detail) msg = err.detail;
      } catch(_) {}
      alert(msg);
      return;
    }

    orderForm.reset();
    quantityInput.value = 1;
    await loadCarsForOrder();  // atualiza estoque exibido
    await loadOrders();
    updateTotal();
  });
}

async function initOrdersPage() {
  if (!orderForm) return;
  await Promise.all([
    loadSellers(),
    loadClients(),
    loadCarsForOrder()
  ]);
  await loadOrders();
}

initOrdersPage();
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

@app.get("/assets/sellers.js", response_class=PlainTextResponse)
def sellers_js():
    return PlainTextResponse(JS_SELLERS, media_type="application/javascript; charset=utf-8")

@app.get("/assets/sales.js", response_class=PlainTextResponse)
def sales_js():
    return PlainTextResponse(JS_SALES, media_type="application/javascript; charset=utf-8")

# ---------- Helpers Gerais ----------
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

def _email_or_400(value: str) -> str:
    v = (value or "").strip()
    if "@" not in v or "." not in v:
        raise HTTPException(status_code=400, detail="E-mail inválido.")
    return v

# ---------- API: Cars ----------
@app.get("/api/cars")
def list_cars(brand: Optional[str] = None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if brand:
                cur.execute(
                    f"""
                    SELECT id, brand, model, year, color, mileage_km, price, quantity, status
                    FROM "{SCHEMA_NAME}".cars
                    WHERE brand ILIKE %s
                    ORDER BY id DESC
                    """,
                    (f"%{brand}%",),
                )
            else:
                cur.execute(
                    f"""
                    SELECT id, brand, model, year, color, mileage_km, price, quantity, status
                    FROM "{SCHEMA_NAME}".cars
                    ORDER BY id DESC
                    """
                )
            rows = cur.fetchall()
        result = []
        for r in rows:
            result.append(
                dict(
                    id=r[0],
                    brand=r[1],
                    model=r[2],
                    year=r[3],
                    color=r[4],
                    mileage_km=r[5] if r[5] is not None else 0,
                    price=float(r[6]),
                    quantity=r[7] if r[7] is not None else 0,
                    status=r[8] or "Ativo",
                )
            )
        return result
    finally:
        conn.close()

@app.post("/api/cars")
def create_car(
    brand: str = Form(...), model: str = Form(...), year: int = Form(...),
    color: str = Form(""), mileage_km: int = Form(0), price: float = Form(...),
    quantity: int = Form(0), status: str = Form("Ativo"),
):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO "{SCHEMA_NAME}".cars
                    (brand, model, year, color, mileage_km, price, quantity, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (brand, model, year, color, mileage_km, price, quantity, status),
            )
            new_id = cur.fetchone()[0]
        conn.commit()
        return {"id": new_id}
    finally:
        conn.close()

@app.put("/api/cars/{car_id}")
def update_car(
    car_id: int,
    brand: str = Form(...), model: str = Form(...), year: int = Form(...),
    color: str = Form(""), mileage_km: int = Form(0), price: float = Form(...),
    quantity: int = Form(0), status: str = Form("Ativo"),
):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f'SELECT 1 FROM "{SCHEMA_NAME}".cars WHERE id = %s',
                (car_id,),
            )
            if not cur.fetchone():
                raise HTTPException(404, "Car not found")

            cur.execute(
                f"""
                UPDATE "{SCHEMA_NAME}".cars
                SET brand=%s, model=%s, year=%s, color=%s,
                    mileage_km=%s, price=%s, quantity=%s, status=%s
                WHERE id=%s
                """,
                (brand, model, year, color, mileage_km, price, quantity, status, car_id),
            )
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()

@app.delete("/api/cars/{car_id}")
def delete_car(car_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f'DELETE FROM "{SCHEMA_NAME}".cars WHERE id = %s',
                (car_id,),
            )
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()

# ---------- API: Clients ----------
@app.get("/api/clients")
def list_clients(nome: Optional[str] = None, cpf: Optional[str] = None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            query = f'SELECT id, nome, cpf, data_nascimento FROM "{SCHEMA_NAME}".clients'
            conditions = []
            params = []
            if nome:
                conditions.append("nome ILIKE %s")
                params.append(f"%{nome}%")
            if cpf:
                digits = "".join(ch for ch in cpf if ch.isdigit())
                if digits:
                    conditions.append("cpf = %s")
                    params.append(digits)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY id DESC"
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
        result = []
        for r in rows:
            dn = r[3]
            result.append(
                dict(
                    id=r[0],
                    nome=r[1],
                    cpf=r[2],
                    data_nascimento=dn.isoformat() if isinstance(dn, date) else str(dn),
                )
            )
        return result
    finally:
        conn.close()

@app.post("/api/clients")
def create_client(
    nome: str = Form(...),
    cpf: str = Form(...),
    data_nascimento: str = Form(...),
):
    conn = get_conn()
    try:
        cpf_digits = _cpf_digits_or_400(cpf)
        dn = _parse_date_or_400(data_nascimento)

        with conn.cursor() as cur:
            cur.execute(
                f'SELECT id FROM "{SCHEMA_NAME}".clients WHERE cpf = %s',
                (cpf_digits,),
            )
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="CPF já cadastrado.")

            cur.execute(
                f"""
                INSERT INTO "{SCHEMA_NAME}".clients (nome, cpf, data_nascimento)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (nome.strip(), cpf_digits, dn),
            )
            new_id = cur.fetchone()[0]
        conn.commit()
        return {"id": new_id}
    finally:
        conn.close()

@app.put("/api/clients/{client_id}")
def update_client(
    client_id: int,
    nome: str = Form(...),
    cpf: str = Form(...),
    data_nascimento: str = Form(...),
):
    conn = get_conn()
    try:
        cpf_digits = _cpf_digits_or_400(cpf)
        dn = _parse_date_or_400(data_nascimento)

        with conn.cursor() as cur:
            cur.execute(
                f'SELECT id FROM "{SCHEMA_NAME}".clients WHERE id = %s',
                (client_id,),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Cliente não encontrado.")

            cur.execute(
                f"""
                SELECT id FROM "{SCHEMA_NAME}".clients
                WHERE cpf = %s AND id <> %s
                """,
                (cpf_digits, client_id),
            )
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="CPF já cadastrado em outro cliente.")

            cur.execute(
                f"""
                UPDATE "{SCHEMA_NAME}".clients
                SET nome = %s, cpf = %s, data_nascimento = %s
                WHERE id = %s
                """,
                (nome.strip(), cpf_digits, dn, client_id),
            )
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()

@app.delete("/api/clients/{client_id}")
def delete_client(client_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f'DELETE FROM "{SCHEMA_NAME}".clients WHERE id = %s',
                (client_id,),
            )
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()

# ---------- API: Sellers ----------
@app.get("/api/sellers")
def list_sellers(
    nome: Optional[str] = None,
    email: Optional[str] = None,
    cpf: Optional[str] = None,
):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            query = f'SELECT id, nome, email, cpf FROM "{SCHEMA_NAME}".sellers'
            conditions = []
            params = []
            if nome:
                conditions.append("nome ILIKE %s")
                params.append(f"%{nome}%")
            if email:
                conditions.append("email ILIKE %s")
                params.append(f"%{email}%")
            if cpf:
                digits = "".join(ch for ch in cpf if ch.isdigit())
                if digits:
                    conditions.append("cpf = %s")
                    params.append(digits)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY id DESC"
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
        result = []
        for r in rows:
            result.append(
                dict(
                    id=r[0],
                    nome=r[1],
                    email=r[2],
                    cpf=r[3],
                )
            )
        return result
    finally:
        conn.close()

@app.post("/api/sellers")
def create_seller(
    nome: str = Form(...),
    email: str = Form(...),
    cpf: str = Form(...),
):
    conn = get_conn()
    try:
        cpf_digits = _cpf_digits_or_400(cpf)
        email_norm = _email_or_400(email)

        with conn.cursor() as cur:
            cur.execute(
                f'SELECT id FROM "{SCHEMA_NAME}".sellers WHERE cpf = %s',
                (cpf_digits,),
            )
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="CPF já cadastrado para outro vendedor.")

            cur.execute(
                f"""
                INSERT INTO "{SCHEMA_NAME}".sellers (nome, email, cpf)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (nome.strip(), email_norm, cpf_digits),
            )
            new_id = cur.fetchone()[0]
        conn.commit()
        return {"id": new_id}
    finally:
        conn.close()

@app.put("/api/sellers/{seller_id}")
def update_seller(
    seller_id: int,
    nome: str = Form(...),
    email: str = Form(...),
    cpf: str = Form(...),
):
    conn = get_conn()
    try:
        cpf_digits = _cpf_digits_or_400(cpf)
        email_norm = _email_or_400(email)

        with conn.cursor() as cur:
            cur.execute(
                f'SELECT id FROM "{SCHEMA_NAME}".sellers WHERE id = %s',
                (seller_id,),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Vendedor não encontrado.")

            cur.execute(
                f"""
                SELECT id FROM "{SCHEMA_NAME}".sellers
                WHERE cpf = %s AND id <> %s
                """,
                (cpf_digits, seller_id),
            )
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="CPF já cadastrado em outro vendedor.")

            cur.execute(
                f"""
                UPDATE "{SCHEMA_NAME}".sellers
                SET nome = %s, email = %s, cpf = %s
                WHERE id = %s
                """,
                (nome.strip(), email_norm, cpf_digits, seller_id),
            )
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()

@app.delete("/api/sellers/{seller_id}")
def delete_seller(seller_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f'DELETE FROM "{SCHEMA_NAME}".sellers WHERE id = %s',
                (seller_id,),
            )
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()

# ---------- API: Orders / Vendas ----------
@app.get("/api/orders")
def list_orders():
    """
    Lista pedidos com:
    - id do carro, descrição e valor unitário;
    - id/nome do vendedor;
    - id/nome do cliente;
    - quantidade, total e data.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    o.id,                 -- 0 id do pedido
                    car.id    AS car_id,  -- 1
                    car.brand,            -- 2
                    car.model,            -- 3
                    car.price,            -- 4 valor unitário
                    o.quantity,           -- 5
                    o.total_value,        -- 6
                    s.id      AS seller_id,   -- 7
                    s.nome    AS seller_name, -- 8
                    c.id      AS client_id,   -- 9
                    c.nome    AS client_name, -- 10
                    o.created_at          -- 11
                FROM "{SCHEMA_NAME}".orders o
                JOIN "{SCHEMA_NAME}".sellers s ON o.seller_id = s.id
                JOIN "{SCHEMA_NAME}".clients c ON o.client_id = c.id
                JOIN "{SCHEMA_NAME}".cars   car ON o.car_id   = car.id
                ORDER BY o.id DESC
                """
            )
            rows = cur.fetchall()
        result = []
        for r in rows:
            dt = r[11]
            result.append(
                dict(
                    id=r[0],
                    car_id=r[1],
                    car_description=f"{r[2]} {r[3]}",
                    car_price=float(r[4]),
                    quantity=r[5],
                    total_value=float(r[6]),
                    seller_id=r[7],
                    seller=r[8],
                    client_id=r[9],
                    client=r[10],
                    created_at=dt.strftime("%Y-%m-%d %H:%M:%S") if isinstance(dt, datetime) else str(dt),
                )
            )
        return result
    finally:
        conn.close()

@app.post("/api/orders")
def create_order(
    seller_id: int = Form(...),
    client_id: int = Form(...),
    car_id: int = Form(...),
    quantity: int = Form(...),
):
    """
    Cria um pedido:
    - valida vendedor, cliente e carro;
    - verifica estoque;
    - calcula valor total;
    - diminui o quantity do carro;
    """
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantidade deve ser positiva.")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Vendedor
            cur.execute(
                f'SELECT id FROM "{SCHEMA_NAME}".sellers WHERE id = %s',
                (seller_id,),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Vendedor não encontrado.")

            # Cliente
            cur.execute(
                f'SELECT id FROM "{SCHEMA_NAME}".clients WHERE id = %s',
                (client_id,),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Cliente não encontrado.")

            # Carro + estoque + preço
            cur.execute(
                f"""
                SELECT id, quantity, price
                FROM "{SCHEMA_NAME}".cars
                WHERE id = %s
                """,
                (car_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Carro não encontrado.")

            car_quantity = row[1] if row[1] is not None else 0
            car_price = float(row[2])

            if car_quantity < quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Estoque insuficiente para o carro selecionado. Disponível: {car_quantity}",
                )

            total_value = car_price * quantity

            # Inserir pedido
            cur.execute(
                f"""
                INSERT INTO "{SCHEMA_NAME}".orders
                    (seller_id, client_id, car_id, quantity, total_value)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (seller_id, client_id, car_id, quantity, total_value),
            )
            new_id = cur.fetchone()[0]

            # Atualizar estoque
            cur.execute(
                f"""
                UPDATE "{SCHEMA_NAME}".cars
                SET quantity = quantity - %s
                WHERE id = %s
                """,
                (quantity, car_id),
            )

        conn.commit()
        return {
            "id": new_id,
            "total_value": total_value,
            "remaining_stock": car_quantity - quantity,
        }
    finally:
        conn.close()

# ---------- Main ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
