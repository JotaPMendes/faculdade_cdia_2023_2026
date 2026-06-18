# Bella Tavola — Docker e05-p02

This folder now contains the Docker deliverables for the second notebook.

Build the image from the source in `../../e02`:

```bash
cd 7_semestre/cdia2/e05/docker
docker build -f Dockerfile -t bella-tavola:e05 ../../e02
```

Run the API container directly:

```bash
docker run -d -p 8000:8000 --name bella-e05 bella-tavola:e05
```

Run the Compose stack:

```bash
docker compose up -d
docker compose logs -f api
docker compose down
```

Run the stack with Nginx on port 80:

```bash
docker compose up -d
curl http://localhost/
curl http://localhost/pratos
docker compose down
```

The stack expects the local Bella Tavola app to provide the API and data paths described in the notebook.
