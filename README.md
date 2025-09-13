\# Projeto CarShop • Impacta



Sistema simples para \*\*cadastro, edição e listagem de carros\*\* (compra e estoque), desenvolvido como parte da disciplina \*\*Projeto de Software\*\*.  

O sistema segue a arquitetura em \*\*3 camadas\*\*: \*\*Front-end (HTML, CSS, JS)\*\*, \*\*Back-end (Python FastAPI)\*\* e \*\*Banco de Dados (PostgreSQL)\*\*.



---



\## 👥 Integrantes



\- Antonio Fabio Lima Silva

 RA: 2302656

---



\## ⚙️ Funcionalidades Entregues

\-### URL Aplicação
\- http://127.0.0.1:8000/

\### Fase 1 — Cadastro de Carros

\- Formulário com 8 campos (marca, modelo, ano, cor, km, preço, quantidade, status).

\- Validação de dados no front (JavaScript) e no back (FastAPI).

\- Salvar novos carros no banco de dados.

\- Listagem em tabela, com filtro por marca.

\- Ações de editar e excluir carros.



\*(Nas próximas fases novas funcionalidades serão adicionadas.)\*



---



\## 💻 Tecnologias



\- \*\*Frontend:\*\* HTML5, CSS3, JavaScript

\- \*\*Backend:\*\* Python 3.11+ com FastAPI

\- \*\*Banco de Dados:\*\* PostgreSQL (schema e tabela criados automaticamente)

\- \*\*ORM:\*\* SQLAlchemy



---



\## 📦 Pré-requisitos



\- Python 3.11+ instalado

\- PostgreSQL instalado e rodando em `localhost:5432`

\- Usuário `postgres` (sem senha por padrão, mas pode configurar senha via `DATABASE\_URL`)



\### Dependências Python

As bibliotecas necessárias são instaladas automaticamente na primeira execução:

\- fastapi

\- uvicorn\[standard]

\- sqlalchemy

\- psycopg2-binary



---



\## ▶️ Como rodar o projeto



1\. Clone o repositório:

&nbsp;  ```bash

&nbsp;  git clone https://github.com/afabiols/ProjetoCarshop.git

&nbsp;  cd ProjetoCarshop



