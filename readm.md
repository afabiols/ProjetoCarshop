CarShop — Catálogo e CRUD de Carros (Fase 1)

Sistema em 3 camadas para uma concessionária simples:

Frontend: HTML + CSS + JavaScript (consumindo a API)

Backend: Python (FastAPI) + SQLAlchemy + Alembic

Banco de Dados: PostgreSQL

Este README cobre a Fase 1 (MVP Catálogo + CRUD de Carros), rodando localmente.
As próximas fases (Vendas/Estoque e Autenticação) serão versionadas com novas tags.

✅ Entregáveis da Fase 1

Catálogo público com filtro por marca (frontend/index.html)

Painel de administração (CRUD de carros) (frontend/admin.html)

API REST (/api/brands, /api/models, /api/cars)

Migrações com Alembic + script de seed

Versionamento no GitHub com tag v0.1-mvp-catalogo

📦 Pré-requisitos

Python 3.10+

Git

PostgreSQL (com pgAdmin opcional)

VS Code (com a extensão Live Server instalada)

🗂️ Estrutura de Pastas (Fase 1)
carshop/
  backend/
    app/
      __init__.py
      config.py
      db.py
      main.py
      models/
        __init__.py
        brand.py
        model.py
        car.py
      routers/
        brands.py
        models.py
        cars.py
    alembic/
      env.py
      versions/
    scripts/
      seed.py
    .env.example
    requirements.txt
  frontend/
    index.html
    admin.html
    css/
      styles.css
    js/
      catalog.js
      admin.js
  .gitignore
  README.md

🗃️ Banco de Dados (PostgreSQL)

Abra o pgAdmin → Query Tool e execute:

CREATE DATABASE carshop;
CREATE USER caruser WITH ENCRYPTED PASSWORD 'carpass';
GRANT ALL PRIVILEGES ON DATABASE carshop TO caruser;

⚙️ Backend (FastAPI)

Terminal do VS Code → navegue até carshop/backend

1) Criar venv e instalar dependências
py -m venv .venv
.venv\Scripts\activate
pip install fastapi uvicorn[standard] sqlalchemy psycopg2-binary alembic pydantic python-dotenv passlib[bcrypt]
pip freeze > requirements.txt

2) Configurar variáveis de ambiente

Copie backend/.env.example para backend/.env e mantenha:

DATABASE_URL=postgresql+psycopg2://caruser:carpass@localhost:5432/carshop
DEBUG=True


Importante: não faça commit de .env. O que vai para o Git é .env.example.

3) Migrar o banco (Alembic)

Inicialize e aponte a URL no alembic.ini:

alembic init alembic


Edite backend/alembic.ini:

sqlalchemy.url = postgresql+psycopg2://caruser:carpass@localhost:5432/carshop


Edite backend/alembic/env.py para importar o Base e os models:

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import Base
from app.models import *  # Brand, Model, Car
target_metadata = Base.metadata


Gere e aplique a migração inicial:

alembic revision --autogenerate -m "init"
alembic upgrade head

4) Popular dados de exemplo (seed)
python -m scripts.seed

5) Subir a API (dev)
uvicorn app.main:app --reload


Swagger: http://127.0.0.1:8000/docs

Teste rápido: http://127.0.0.1:8000/api/brands

🎨 Frontend (HTML + CSS + JavaScript)

O front é estático (HTML/JS) e consome a API local.

1) Live Server

No VS Code, instale a extensão Live Server (Ritwick Dey)

Clique com o botão direito em frontend/index.html → Open with Live Server

Normalmente abre em http://127.0.0.1:5500

2) Páginas

Catálogo: frontend/index.html
Lista carros com filtro por marca (consome GET /api/brands e GET /api/cars).

Admin: frontend/admin.html
CRUD de carros (usa POST/PUT/DELETE /api/cars + GET /api/brands/GET /api/models).

Observação: nesta fase não há login; o foco é demonstrar a camada de front consumindo a API.

🔌 Endpoints (Fase 1)
Método	Endpoint	Descrição
GET	/api/brands	Lista marcas
POST	/api/brands	Cria marca (name)
PUT	/api/brands/{id}	Atualiza marca (name)
DELETE	/api/brands/{id}	Remove marca
GET	/api/models	Lista modelos (opcional brand_id)
POST	/api/models	Cria modelo (name, brand_id)
PUT	/api/models/{id}	Atualiza modelo
DELETE	/api/models/{id}	Remove modelo
GET	/api/cars	Lista carros (opcional brand_id)
POST	/api/cars	Cria carro
PUT	/api/cars/{id}	Atualiza carro
DELETE	/api/cars/{id}	Remove carro

Campos do carro (POST/PUT):
brand_id, model_id, year, price, color, mileage_km, quantity, status

🧪 Teste Rápido (Fluxo sugerido)

Suba a API (uvicorn ... --reload)

Rode o seed uma vez (python -m scripts.seed)

Abra o front:

frontend/index.html (Live Server) → veja o catálogo

frontend/admin.html → crie/edite/exclua carros

Volte ao Catálogo e confira a atualização

🧭 Git & GitHub (Fase 1)
1) Iniciar repositório (apenas na primeira vez)
git init


Crie o .gitignore na raiz:

.venv/
__pycache__/
.env
.DS_Store

2) Commitar e subir
git add .
git commit -m "feat: Fase 1 - Catálogo + CRUD de carros (front HTML/CSS/JS + FastAPI + PostgreSQL)"
git branch -M main
git remote add origin https://github.com/<seu-usuario>/carshop.git
git push -u origin main

3) Tag da Fase 1
git tag v0.1-mvp-catalogo
git push origin v0.1-mvp-catalogo

🎥 Roteiro para o Vídeo (Fase 1) — 3 a 5 min

Objetivo (15s): explicar que é Fase 1 de um sistema 3 camadas.

Arquitetura (30s): front (HTML/JS) → API FastAPI → PostgreSQL.

Execução (60s):

Mostrar uvicorn app.main:app --reload

Abrir index.html (Live Server) → catálogo e filtro por marca

Abrir admin.html → criar/editar/excluir um carro

Voltar ao catálogo e mostrar atualização

Repositório (30s): mostrar GitHub com tag v0.1-mvp-catalogo.

Encerramento (15s): dizer que Fase 2 terá Vendas + Estoque.

🛠️ Solução de Problemas (FAQ)

1) CORS bloqueando?

O backend já vem com CORSMiddleware permitindo origins=["*"] para desenvolvimento.

Garanta que o front está sendo servido com Live Server (porta 5500, por exemplo).

2) Alembic não encontra os models (target_metadata=None)?

Revise alembic/env.py: precisa importar Base e app.models.* e ajustar o sys.path.

3) Erro de conexão no PostgreSQL?

Verifique o serviço do Postgres e a DATABASE_URL no .env.

Teste a conexão no pgAdmin com o mesmo usuário/senha.

4) API sobe, mas o front não carrega nada?

Veja o console do navegador (F12 → Console/Network).

Verifique o valor da constante API nos HTMLs (está como http://127.0.0.1:8000/api).

🧱 Próximas Fases (Visão)

Fase 2 (v0.2-vendas-estoque): entidades Customer, Sale, StockMove; registrar venda, abater estoque e relatórios.

Fase 3 (v1.0-release): autenticação (admin/seller), proteção das rotas, polimento e exportações.

📜 Licença

Uso acadêmico/educacional.

🧑‍💻 Autor

Projeto acadêmico — Fase 1 por Seu Nome.
Contato: seu-email@exemplo.com
.

📎 Anexos (opcional para o README)

Screenshots sugeridos:

backend/docs_swagger.png — mostrando /docs

frontend/catalogo.png — lista de carros

frontend/admin.png — CRUD de carros

Dica: salve as imagens em docs/ e referencie no README:
![Catálogo](docs/catalogo.png)

Se quiser, posso gerar um checklist em PDF dessa Fase 1 pra você anexar ao repositório e usar como guia na apresentação. Quer que eu crie?