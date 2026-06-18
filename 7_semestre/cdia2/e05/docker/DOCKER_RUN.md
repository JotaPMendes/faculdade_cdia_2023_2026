# Bella Tavola — Docker (e05 p2)

This folder contains the Docker artifacts for e05-p2:

- hardened multi-stage `Dockerfile` with non-root runtime user
- `docker-compose.yml` for API + PostgreSQL + Nginx
- `nginx.conf` reverse proxy entrypoint

The API source code used by the Docker build is in `7_semestre/cdia2/e03`.

## 1) Build the image directly

```bash
cd 7_semestre/cdia2/e05/docker
docker build -f Dockerfile -t bella-tavola:e05-p2 ../../e03
```

Run and validate directly:

```bash
docker run --rm -p 8000:8000 bella-tavola:e05-p2
curl http://localhost:8000/
curl http://localhost:8000/ml/health
```

## 2) Run the full stack with Compose

```bash
cd 7_semestre/cdia2/e05/docker
docker compose up -d --build
```

Validate through Nginx (port 80):

```bash
curl http://localhost/
curl http://localhost/ml/health
```

If you have Hugging Face credentials set in your shell (`HF_TOKEN` and `HF_REPO_ID`), you can also test prediction:

```bash
curl -X POST http://localhost/ml/predict \
	-H "Content-Type: application/json" \
	-d '{
		"valor_transacao": 150.0,
		"hora_transacao": 14,
		"distancia_ultima_compra": 5.0,
		"tentativas_senha": 1,
		"pais_diferente": 0,
		"device_risk_score": 0.25
	}'
```

## 3) Inspect and shutdown

```bash
docker compose ps
docker compose logs -f api
docker compose down
```

If you also want to remove PostgreSQL data volume:

```bash
docker compose down -v
```
