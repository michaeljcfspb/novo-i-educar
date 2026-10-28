# 05 — Deploy com Docker e Easypanel

## 1. Antes de subir

Checklist de produção:

- [ ] `DJANGO_SECRET_KEY` única e forte (`python -c "import secrets; print(secrets.token_urlsafe(50))"`).
- [ ] `DJANGO_DEBUG=False`.
- [ ] `DJANGO_ALLOWED_HOSTS` com o domínio real (sem `*`).
- [ ] `DJANGO_CSRF_TRUSTED_ORIGINS` com `https://seudominio.com.br`.
- [ ] `DJANGO_SECURE_COOKIES=True` (exige HTTPS no proxy).
- [ ] Senha do PostgreSQL forte e volume persistente.
- [ ] Remover `DJANGO_SUPERUSER_PASSWORD` do ambiente depois do primeiro boot.

O `entrypoint.sh` já executa, a cada deploy: espera o banco → `migrate` → `collectstatic` →
Gunicorn. É seguro reiniciar quantas vezes for preciso.

## 2. Preparar o repositório

```bash
git init
git add .
git commit -m "feat: reescrita i-Educar (React + Django)"
git remote add origin git@github.com:SEU_USUARIO/ieducar-react-django.git
git push -u origin main
```

> O arquivo `.env` está no `.gitignore`. Somente `.env.example` vai para o repositório.

## 3. Easypanel — opção A (Compose, recomendada)

1. **Criar projeto**: Easypanel → *Projects* → **Create Project** → nome `ieducar`.
2. **Novo serviço**: **+ Service** → **Compose**.
3. **Fonte**: *GitHub* → selecione o repositório e a branch `main`.
4. **Arquivo**: `docker-compose.yml` (raiz do repositório).
5. **Variáveis de ambiente**: cole o conteúdo de `.env.example` ajustado. Mínimo:

```env
DJANGO_SECRET_KEY=...
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=ieducar.seudominio.com.br,backend
DJANGO_CSRF_TRUSTED_ORIGINS=https://ieducar.seudominio.com.br
DJANGO_SECURE_COOKIES=True
POSTGRES_DB=ieducar
POSTGRES_USER=ieducar
POSTGRES_PASSWORD=...
POSTGRES_HOST=db
POSTGRES_PORT=5432
DJANGO_SUPERUSER_EMAIL=admin@seudominio.com.br
DJANGO_SUPERUSER_PASSWORD=...
```

6. **Volumes**: garantir `postgres_data` (dados), `media_data` (fotos) e `static_data`.
   No Easypanel, volumes nomeados do Compose são criados automaticamente; para backup
   gerenciado, troque por *Mounts* apontando para um diretório persistente.
7. **Domínio**: aba **Domains** do serviço `frontend` → adicione
   `ieducar.seudominio.com.br`, porta **80**, e habilite **HTTPS (Let's Encrypt)**.
8. **Deploy**. Acompanhe os logs de `backend` (migrações) e `frontend` (build do Vite).

## 4. Easypanel — opção B (serviços separados)

Útil para escalar backend e frontend de forma independente.

| Serviço | Tipo | Build | Porta | Observações |
| ------- | ---- | ----- | ----- | ----------- |
| `db` | PostgreSQL (App) | imagem gerenciada | 5432 | usuário/banco `ieducar`; volume persistente |
| `backend` | App | Dockerfile `backend/Dockerfile` | 8000 | env do Django; volume para `/app/media` |
| `frontend` | App | Dockerfile `frontend/Dockerfile` | 80 | domínio público; proxy interno para `backend:8000` |

Nesse modo, os serviços precisam estar na **mesma rede** do projeto Easypanel e o serviço do
backend deve se chamar `backend` para o `nginx.conf` resolver `http://backend:8000`.
Se o nome mudar, ajuste `nginx.conf` (ou use a variável de ambiente do upstream).

## 5. Verificação pós-deploy

```bash
curl -fsS https://ieducar.seudominio.com.br/api/v1/health/
# {"status": "ok", "banco": "ok"}

curl -I https://ieducar.seudominio.com.br/api/docs/
# 200 OK
```

No navegador: login em `https://ieducar.seudominio.com.br`, criar aluno, criar matrícula e
enturmar em uma turma.

## 6. Backup e restauração

Backup do banco (agende no Easypanel ou cron externo):

```bash
docker compose exec -T db pg_dump -U ieducar -Fc ieducar > backup-$(date +%F).dump
```

Restauração:

```bash
docker compose exec -T db pg_restore -U ieducar -d ieducar --clean --if-exists < backup-2026-10-28.dump
```

Arquivos de mídia (`media_data`) precisam de backup separado (rsync ou storage S3).

## 7. Atualização e rollback

- **Atualizar**: `git push` → Easypanel *Deploy* (ou habilitar auto-deploy no GitHub).
- **Migrações**: rodam automaticamente no start do backend.
- **Rollback**: Easypanel → *Deployments* → redeploy da versão anterior. Se a migração for
  incompatível, restaure o backup do banco antes.

## 8. Operação

- **Logs**: aba *Logs* de cada serviço; Gunicorn escreve access log no stdout.
- **Escala**: aumente `--workers` do Gunicorn ou réplicas do `backend`; o `frontend` é estático.
- **Métricas**: use o healthcheck `/api/v1/health/` no monitoramento do Easypanel.
- **Segurança**: HTTPS obrigatório, `DEBUG=False`, banco sem porta pública, segredos só no Easypanel.

## 9. Desenvolvimento local com Docker

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec backend python manage.py seed_demo
# http://localhost:8080
```

Para rodar somente o banco e usar os servidores locais:

```bash
docker compose up -d db
# backend: DB_ENGINE=postgres POSTGRES_HOST=127.0.0.1 python manage.py runserver
# frontend: npm run dev
```
