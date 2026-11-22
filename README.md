# StockFlow

Aplicativo local de controle de estoque, vendas e caixa.

## Componentes

- `frontend/`: interface React com Vite.
- `backend/`: API FastAPI.
- `docker-compose.yml`: PostgreSQL para desenvolvimento local.

## Executar localmente

1. Suba o banco: `docker compose up -d postgres`.
2. Em um terminal, instale e inicie a API:

   ```powershell
   cd backend
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

3. Em outro terminal, instale e inicie a interface:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

A interface fica em `http://localhost:5173` e a documentação da API em `http://localhost:8000/docs`.

O backend usa a conexão local configurada em `DATABASE_URL` ou, na ausência dela, o banco definido no `docker-compose.yml`. Não use as credenciais de desenvolvimento em produção.

## Vendas e relatórios

Vendas podem combinar produtos cadastrados, que baixam do estoque, com itens avulsos, que não alteram o estoque. Cada venda registra o vendedor. O dashboard permite filtrar por período, produto e vendedor.
