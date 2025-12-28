# PINN Benchmark: Full-Stack Edition 🚀

Uma plataforma robusta para benchmarking de **Physics-Informed Neural Networks (PINNs)** contra Métodos de Elementos Finitos (FEM) em geometrias complexas.

![Dashboard Preview](https://via.placeholder.com/800x400?text=Dashboard+Preview)

## 🌟 Funcionalidades

*   **Interface Moderna**: Dashboard em React + TypeScript com tema Dark/Glassmorphism.
*   **Controle Total**: Edite configurações de física e hiperparâmetros via UI.
*   **Visualização 3D**: Renderização interativa de malhas e soluções (Geometry-Aware).
*   **Logs em Tempo Real**: Acompanhe o treinamento ao vivo via WebSocket.
*   **Arquitetura Modular**: Separação clara entre Core (Python), Backend (FastAPI) e Frontend (Vite).

## 🛠️ Stack Tecnológica

*   **Core**: DeepXDE, TensorFlow, Scipy, Gmsh.
*   **Backend**: FastAPI, Uvicorn, WebSockets.
*   **Frontend**: React, Vite, TailwindCSS, Recharts, Plotly.

## 🚀 Como Rodar (Quickstart)

Certifique-se de ter Python 3.10+ e Node.js 18+ instalados.

1.  **Instale as dependências Python:**
    ```bash
    uv pip install -r requirements.txt
    uv pip install -r backend/requirements.txt
    ```

2.  **Instale as dependências do Frontend:**
    ```bash
    cd frontend
    npm install
    cd ..
    ```

3.  **Inicie a Aplicação (Tudo em um):**
    ```bash
    python3 start_app.py
    ```
    Isso abrirá o navegador automaticamente em `http://localhost:5173`.

## 📂 Estrutura do Projeto

*   `/backend`: API Server (FastAPI).
*   `/frontend`: Web App (React).
*   `/models`: Implementações PINN/FEM.
*   `/problems`: Definições de Física/Geometria.
*   `/utils`: Ferramentas auxiliares.
*   `/docs`: Documentação detalhada (`LEARNINGS.md`, `ARCHITECTURE.md`).

## 📚 Documentação

*   [Aprendizados Técnicos (DeepXDE & Singularidades)](docs/LEARNINGS.md)
*   [Arquitetura do Sistema](docs/ARCHITECTURE.md)

## 🧪 Benchmarks Disponíveis

1.  **Electrostatic Mesh**: Estator de Motor, Placa com Furos, L-Shape.
2.  **Poisson 2D**: Validação analítica.
3.  **Heat/Wave 1D**: Problemas dependentes do tempo.
