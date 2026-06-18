# Bella Tavola — Docker (moved for notebook e05)

The Docker artifacts for the e05 notebook were moved here. The application source code remains in `7_semestre/cdia2/e02`.

docker build -f Dockerfile -t bella-tavola:e02 ../e02
Build image (use this Dockerfile and the project code in `../../e02` as build context):

```bash
cd 7_semestre/cdia2/e05/docker
# Dockerfile is in this folder, project source (requirements.txt, main.py) is in ../../e02
docker build -f Dockerfile -t bella-tavola:e05 ../../e02
```

Run container (detached, map port 8000):

```bash
docker run -d -p 8000:8000 --name bella-e05 bella-tavola:e05
```

Run container interactively (remove on exit):

```bash
docker run --rm -it -p 8000:8000 bella-tavola:e05
```

Stop and remove container:

```bash
docker stop bella-e05 && docker rm bella-e05
```

View logs:

```bash
docker logs -f bella-e05
```
