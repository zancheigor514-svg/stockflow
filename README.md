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

Antes de iniciar a API pela primeira vez com esta versão, preencha `STOCKFLOW_ADMIN_USERNAME` e `STOCKFLOW_ADMIN_PASSWORD` no `.env` da raiz. Não use a senha de exemplo do PostgreSQL para uma loja real.

A interface fica em `http://localhost:5173` e a documentação local da API em `http://localhost:8000/docs`.

O backend usa a conexão local configurada em `DATABASE_URL` ou, na ausência dela, o banco definido no `docker-compose.yml`. Não use as credenciais de desenvolvimento em produção.

## Acesso e segurança

- O primeiro início agora exige `STOCKFLOW_ADMIN_USERNAME` e `STOCKFLOW_ADMIN_PASSWORD` no `.env` da raiz. Use uma senha única com pelo menos 14 caracteres; ela é guardada no banco como hash Argon2id. Depois, altere-a em **Segurança** e remova a senha inicial do `.env`. Instale as dependências do backend com `pip install -r requirements.txt`.
- O login usa cookie de sessão HttpOnly, com validade de 8 horas. Em desenvolvimento local, `AUTH_COOKIE_SECURE=false`; em produção, use HTTPS e `AUTH_COOKIE_SECURE=true`. O modo `APP_ENV=production` exige cookie seguro e senha exclusiva do banco, e desativa a documentação interativa da API.
- O PostgreSQL agora publica a porta apenas em `127.0.0.1`; o backend no mesmo computador continua acessando-o, mas outros dispositivos não devem conectar-se diretamente ao banco.
- Para acessar do celular de qualquer lugar, hospede frontend e API sob o mesmo domínio HTTPS (por exemplo, encaminhando `/api` à API) ou use uma VPN privada. Não encaminhe portas do roteador para Uvicorn ou PostgreSQL. Em produção, configure `FRONTEND_ORIGINS` com a origem HTTPS exata, `ALLOWED_HOSTS` com o domínio do app e `VITE_API_URL=/api` antes de compilar o frontend.
- A lista de tentativas de login é limitada no processo da API. Se a hospedagem usar vários processos, configure também limite de tentativas no proxy/serviço de borda.
- A autenticação atual é uma conta administrativa única. Para atribuir ações a cada funcionário, ainda será necessário criar contas individuais e permissões.

Gere uma senha inicial com `python -c "import secrets; print(secrets.token_urlsafe(24))"` e cole-a somente no `.env` local.

## Vendas e relatórios

Vendas podem combinar produtos cadastrados, que baixam do estoque, com itens avulsos, que não alteram o estoque. Cada venda registra o vendedor. O dashboard permite filtrar por período, produto e vendedor.

## Crediário e cartão

- Em **Crediário**, cadastre o cliente com CPF válido, RG, nome e endereço. As fotos do documento, da pessoa e do comprovante são opcionais. O ID numérico é gerado pelo banco e identifica o cliente.
- No carrinho, escolha **Crediário**, informe o ID do cliente, o valor pago na hora e a quantidade de parcelas (de 1 a 120) para financiar o saldo. Cada parcela recebe um ID próprio. O primeiro vencimento fica 30 dias após a venda; os seguintes são espaçados em mais 30 dias.
- Para receber parcelas vencidas, abra a conta do cliente, marque uma ou mais parcelas e registre o pagamento. A data e a hora do pagamento são guardadas no histórico e na parcela. O backend calcula juros simples de 1% ao mês, proporcional aos dias de atraso (1% ÷ 30 × dias), arredondados para centavos. Não há juros antes do vencimento.
- Em **Vendedoras**, adicione, renomeie e remova as opções que aparecem na seleção do vendedor responsável pelas vendas. A lista inicial é Loja e Luana.
- No cartão de crédito, registre de 1 a 36 parcelas sem acréscimo adicional pelo StockFlow. O total da venda não muda; o histórico mostra o número de parcelas.

Os dados do cliente e as imagens ficam no PostgreSQL e são incluídos nos dumps. A API exige login; a conta atual é única e ainda não separa permissões por funcionário. Não exponha a API até configurar hospedagem HTTPS, domínio permitido e limitação de tentativas no proxy. Proteja também os arquivos de backup, que contêm documentos pessoais.

## Dados da loja

Abra **Minha loja** na navegação para alterar o nome e enviar um logotipo PNG, JPG ou WebP de até 3 MB. O nome e os bytes da imagem ficam no PostgreSQL e são incluídos no backup do banco.

## Persistência e backups

- O PostgreSQL usa o volume nomeado `stockflow_data`, que mantém os dados ao reiniciar ou recriar o contêiner. `docker compose down` preserva o volume; **não use `docker compose down -v`**, pois `-v` apaga o volume.
- O serviço `backup` cria um dump compactado assim que inicia, verifica se o arquivo pode ser lido e repete a cada 24 horas. Mantém os últimos 30 dias em `backups/`, pasta ignorada pelo Git. A frequência e retenção podem ser ajustadas por `BACKUP_INTERVAL_SECONDS` e `BACKUP_RETENTION_DAYS` no `.env`.
- Consulte o serviço com `docker compose logs -f backup`. Espere a mensagem `Backup concluído` e confira se há arquivos `.dump` em `backups/`.
- Cópias no mesmo computador não protegem contra perda ou falha do disco. Sincronize periodicamente a pasta `backups/` para outro dispositivo ou armazenamento em nuvem.
- Os dumps contêm CPFs, endereços e, se enviados, fotos. Proteja a pasta com criptografia do disco e criptografe as cópias antes de enviá-las para outro local.

Para restaurar um dump, pare a API e escolha um arquivo de `backups/`. O comando abaixo substitui os objetos correspondentes no banco `stockflow`, então faça uma cópia do estado atual antes de executá-lo:

```powershell
docker compose exec backup pg_restore --host=postgres --username=stockflow --dbname=stockflow --clean --if-exists --no-owner --no-privileges /backups/stockflow_YYYYMMDDTHHMMSSZ.dump
```

O formato custom do `pg_dump` é restaurado com `pg_restore`. Veja a documentação do PostgreSQL para [pg_dump](https://www.postgresql.org/docs/16/app-pgdump.html) e [pg_restore](https://www.postgresql.org/docs/16/app-pgrestore.html).

O arquivo `.env.example` contém apenas valores de desenvolvimento. Use uma senha forte e exclusiva antes de expor qualquer serviço à internet.
