# Arquitetura do Sistema

O projeto evoluiu de scripts isolados para uma aplicação Full-Stack moderna.

## 🏗️ Visão Geral

```mermaid
graph TD
    User[Usuário] --> Frontend[Frontend (React + Vite)]
    Frontend -->|HTTP/WS| Backend[Backend (FastAPI)]
    Backend -->|Subprocess| Core[Core Engine (Python)]
    Core -->|Read/Write| Config[config.py]
    Core -->|Write| Results[results/latest/]
    Frontend -->|Read| Results
```

## 🧩 Componentes

### 1. Frontend (`/frontend`)
*   **Tecnologia:** React, TypeScript, Vite, TailwindCSS.
*   **Responsabilidade:** Interface do usuário, visualização de gráficos, editor de configuração.
*   **Comunicação:** Consome API REST do Backend e WebSocket para logs em tempo real.

### 2. Backend (`/backend`)
*   **Tecnologia:** FastAPI, Uvicorn.
*   **Responsabilidade:**
    *   Expor endpoints para leitura/escrita de `config.py`.
    *   Gerenciar a execução do `main.py` (Core) em background.
    *   Streaming de logs via WebSocket.

### 3. Core Engine (`/`)
*   **Scripts Principais:** `main.py`, `models/`, `problems/`.
*   **Tecnologia:** DeepXDE, TensorFlow, Scipy.
*   **Responsabilidade:** Treinamento das PINNs, resolução FEM, geração de malhas.
*   **Entrada:** `config.py`.
*   **Saída:** Arquivos em `results/latest/` (JSON, PNG, HTML).

## 📂 Estrutura de Diretórios

*   `backend/`: Código do servidor API.
*   `frontend/`: Código da interface web.
*   `models/`: Implementação das Redes Neurais e Solvers FEM.
*   `problems/`: Definição das EDPs e Geometrias.
*   `utils/`: Scripts auxiliares (geração de malha, plotagem).
*   `meshes/`: Arquivos `.msh` e visualizações.
*   `results/`: Artefatos gerados (métricas, relatórios).
*   `docs/`: Documentação técnica.
