👥 Integrantes

Antonio Fabio Lima Silva
RA: 2302656

Video - caso o youtube não abra devido a políticas internas



⚙️ Funcionalidades Entregues
URL da Aplicação

http://127.0.0.1:8000/

Dashboard

Tela inicial com botões para Carros, Clientes, Vendas (placeholder) e Vendedores (placeholder).

Fase 1 — Cadastro de Carros

Formulário com 8 campos (marca, modelo, ano, cor, km, preço, quantidade, status).

Validação no front (JavaScript) e back (FastAPI).

Salvar, listar com filtro por marca, editar e excluir.

Fase 2 — Cadastro de Clientes

Formulário simples (nome, CPF, data de nascimento).

CPF salvo apenas com dígitos (11) e unicidade garantida.

Listar com filtro por nome e/ou CPF, editar e excluir.

(Próximas fases: Vendas e Vendedores.)

💻 Tecnologias

Frontend: HTML5, CSS3, JavaScript

Backend: Python 3.11+ com FastAPI

Banco de Dados: PostgreSQL (auto-setup de database e schema)

ORM: SQLAlchemy

📦 Pré-requisitos

Python 3.11+

PostgreSQL rodando em localhost:5432

Usuário postgres (ajuste via DATABASE_URL se usar senha/usuário diferente)

Dependências Python

As bibliotecas são instaladas automaticamente na primeira execução, mas você pode usar requirements.txt:

fastapi
uvicorn[standard]
sqlalchemy
pydantic
psycopg2-binary

▶️ Como rodar o projeto
1) Clonar o repositório
git clone https://github.com/afabiols/ProjetoCarshop.git
cd ProjetoCarshop

2) (Opcional) Criar e ativar a venv

Windows (PowerShell):

python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt


Linux/macOS:

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


Se não usar requirements.txt, o app faz auto-instalação na primeira execução.

3) Configurar variáveis (opcional)

Crie um arquivo .env (ou exporte no ambiente) se quiser sobrescrever os padrões:

DATABASE_URL=postgresql+psycopg2://postgres@localhost:5432/carshop
DB_SCHEMA=carshop


O app cria o database e o schema automaticamente se não existirem.

4) Executar

Opção A (uvicorn):

uvicorn app:app --reload


Opção B (python):

python app.py


Acesse:

Dashboard: http://127.0.0.1:8000/

Carros: http://127.0.0.1:8000/cars

Clientes: http://127.0.0.1:8000/clients

Vendas (placeholder): http://127.0.0.1:8000/sales

Vendedores (placeholder): http://127.0.0.1:8000/sellers

🔐 Variáveis de Ambiente

DATABASE_URL — Ex.: postgresql+psycopg2://postgres@localhost:5432/carshop

DB_SCHEMA — Ex.: carshop (default)

Importante: não commitar .env. Mantenha .env no .gitignore.

🔗 Endpoints (API)
Carros

GET /api/cars?brand=Toyota — lista (filtro opcional por marca)

POST /api/cars — cria (form fields: brand, model, year, color, mileage_km, price, quantity, status)

PUT /api/cars/{id} — atualiza

DELETE /api/cars/{id} — remove

Clientes

GET /api/clients?nome=Maria&cpf=12345678901 — lista (filtros opcionais)

POST /api/clients — cria (form fields: nome, cpf(11 dígitos), data_nascimento (YYYY-MM-DD))

PUT /api/clients/{id} — atualiza

DELETE /api/clients/{id} — remove

🗂️ Estrutura do Projeto
ProjetoCarshop/
├─ app.py                # monolito FastAPI + HTML/CSS/JS embutidos
├─ requirements.txt      # dependências (opcional)
├─ .gitignore            # ignora venv/.env/artefatos
├─ .gitattributes        # normalização de EOL
└─ README.md             # este arquivo

🧪 Teste rápido de conexão (PostgreSQL)

Se tiver erro de conexão:

Verifique se o serviço PostgreSQL está ativo.

Teste credenciais com psql/DBeaver.

Confira DATABASE_URL (usuário, senha, host, porta e database).

Exemplo com senha:

DATABASE_URL=postgresql+psycopg2://postgres:MINHA_SENHA@localhost:5432/carshop

❗ Troubleshooting

psycopg2-binary falhou ao instalar:
Atualize pip/setuptools: python -m pip install --upgrade pip setuptools wheel

Permissão negada ao criar database:
Rode o servidor com um usuário PostgreSQL com permissão para CREATE DATABASE ou crie o DB manualmente.

Porta 8000 ocupada:
Rode em outra porta: uvicorn app:app --reload --port 8001

CPF inválido:
O backend exige 11 dígitos. Remova máscara/pontos/traços.

Extensão para Diagrama PlanUML

View para consulta de vendas

SELECT
    o.id                    AS id_pedido,
    o.created_at            AS data_pedido,

    -- Carro
    car.id                  AS id_carro,
    car.brand               AS marca_carro,
    car.model               AS modelo_carro,
    car.year                AS ano_carro,
    car.color               AS cor_carro,
    car.price               AS preco_unitario,
    car.quantity            AS estoque_atual,

    -- Cliente
    c.id                    AS id_cliente,
    c.nome                  AS nome_cliente,
    c.cpf                   AS cpf_cliente,
    c.data_nascimento       AS data_nascimento_cliente,

    -- Vendedor
    s.id                    AS id_vendedor,
    s.nome                  AS nome_vendedor,
    s.email                 AS email_vendedor,
    s.cpf                   AS cpf_vendedor,

    -- Dados do pedido
    o.quantity              AS quantidade_vendida,
    o.total_value           AS valor_total
FROM carshop.orders  o
JOIN carshop.cars    car ON o.car_id    = car.id
JOIN carshop.clients c   ON o.client_id = c.id
JOIN carshop.sellers s   ON o.seller_id = s.id;

📝 Licença

MIT — sinta-se à vontade para usar e adaptar.