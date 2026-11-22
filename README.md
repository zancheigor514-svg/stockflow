# StockFlow

Aplicativo local de controle de estoque, vendas e caixa.

## Componentes

- `frontend/`: interface React com Vite.
- `backend/`: API FastAPI.
- `docker-compose.yml`: PostgreSQL para desenvolvimento local.

## Executar localmente

1. Crie sua configuração local: `Copy-Item .env.example .env`.
2. Suba o banco e o serviço de backup: `docker compose up -d`.
3. Em um terminal, instale e inicie a API:

   ```powershell
   cd backend
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

4. Em outro terminal, instale e inicie a interface:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

A interface fica em `http://localhost:5173` e a documentação da API em `http://localhost:8000/docs`.

O backend usa a conexão local configurada em `DATABASE_URL` ou, na ausência dela, o banco definido no `docker-compose.yml`. Não use as credenciais de desenvolvimento em produção.

## Vendas e relatórios

Vendas podem combinar produtos cadastrados, que baixam do estoque, com itens avulsos, que não alteram o estoque. Cada venda registra o vendedor. O dashboard permite filtrar por período, produto e vendedor.

## Dados da loja

Abra **Minha loja** na navegação para alterar o nome e enviar um logotipo PNG, JPG ou WebP de até 3 MB. O nome e os bytes da imagem ficam no PostgreSQL e são incluídos no backup do banco.

## Persistência e backups

- O PostgreSQL usa o volume nomeado `stockflow_data`, que mantém os dados ao reiniciar ou recriar o contêiner. `docker compose down` preserva o volume; **não use `docker compose down -v`**, pois `-v` apaga o volume.
- O serviço `backup` cria um dump compactado assim que inicia e repete a cada 24 horas. Mantém os últimos 30 dias em `backups/`, pasta ignorada pelo Git. A frequência e retenção podem ser ajustadas por `BACKUP_INTERVAL_SECONDS` e `BACKUP_RETENTION_DAYS` no `.env`.
- Consulte o serviço com `docker compose logs -f backup`. Espere a mensagem `Backup concluído` e confira se há arquivos `.dump` em `backups/`.
- Cópias no mesmo computador não protegem contra perda ou falha do disco. Sincronize periodicamente a pasta `backups/` para outro dispositivo ou armazenamento em nuvem.

Para restaurar um dump, pare a API e escolha um arquivo de `backups/`. O comando abaixo substitui os objetos correspondentes no banco `stockflow`, então faça uma cópia do estado atual antes de executá-lo:

```powershell
docker compose exec backup pg_restore --host=postgres --username=stockflow --dbname=stockflow --clean --if-exists --no-owner --no-privileges /backups/stockflow_YYYYMMDDTHHMMSSZ.dump
```

O formato custom do `pg_dump` é restaurado com `pg_restore`. Veja a documentação do PostgreSQL para [pg_dump](https://www.postgresql.org/docs/16/app-pgdump.html) e [pg_restore](https://www.postgresql.org/docs/16/app-pgrestore.html).

O arquivo `.env.example` contém apenas valores de desenvolvimento. Use uma senha forte e exclusiva antes de expor qualquer serviço à internet.
