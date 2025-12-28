import os
import json
import sys
import shutil

# Adicionar raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONFIG
from utils.checkpoint import CheckpointManager

def generate_report():
    print("="*50)
    print("GERADOR DE RELATÓRIO FINAL")
    print("="*50)
    
    # Encontrar o último run com metrics.json
    base_dir = os.path.join("checkpoints", CONFIG["problem"])
    if not os.path.exists(base_dir):
        print(f"❌ Diretório base não encontrado: {base_dir}")
        return

    runs = sorted([d for d in os.listdir(base_dir) if d.startswith("run_")])
    
    run_dir = None
    for run in reversed(runs):
        path = os.path.join(base_dir, run)
        if os.path.exists(os.path.join(path, "metrics.json")):
            run_dir = path
            break
            
    if run_dir is None:
        print("❌ Nenhum run com métricas encontrado.")
        return

    print(f"✓ Diretório do Run Selecionado: {run_dir}")
    
    # Carregar Métricas
    metrics_path = os.path.join(run_dir, "metrics.json")
    metrics = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
            
    def fmt(val):
        try:
            return f"{float(val):.4f}"
        except:
            return "N/A"
    
    # Caminhos dos Artefatos
    html_path = "visualization.html" # Link relativo no results/latest
    png_path = "comparison.png"
    mesh_name = os.path.basename(CONFIG["mesh_file"])
    
    # Conteúdo do Relatório (Genérico)
    title = f"Relatório Final: PINN vs FEM ({mesh_name})"
    desc = f"Experimento simulando distribuição de potencial na malha `{mesh_name}`."

    report_content = f"""# {title}

## 1. Visão Geral
{desc}

**Objetivo**: Comparar a solução contínua da PINN com a discreta do FEM.

## 2. Configuração
- **Problema**: {CONFIG['problem']}
- **Malha**: `{mesh_name}`
- **Condições de Contorno**:
{json.dumps(CONFIG.get('boundary_conditions', {}), indent=4)}

### Parâmetros da PINN
- **Arquitetura**: FNN (Fully Connected)
- **Camadas**: [2, 50, 50, 50, 50, 1]
- **Ativação**: tanh
- **Otimizador**: Adam + L-BFGS

## 3. Resultados Quantitativos (MAE)
Abaixo o Erro Médio Absoluto (MAE) comparado ao FEM (Ground Truth numérico):

| Modelo | MAE (V) |
| :--- | :--- |
| **PINN** | **{fmt(metrics.get('PINN', 'N/A'))}** |
| RF (Random Forest) | {fmt(metrics.get('RF', 'N/A'))} |
| XGBoost | {fmt(metrics.get('XGB', 'N/A'))} |

> **Nota**: O erro da PINN é esperado ser maior que zero pois ela aprende a física, não copia o FEM. O FEM tem erro de discretização que a PINN tenta superar (suavidade).

## 4. Visualização Interativa
### [>> ABRIR VISUALIZAÇÃO INTERATIVA <<]({html_path})
*(Baixe este arquivo para visualizar ou use um visualizador de HTML)*

## 5. Artefatos Gerados
- **Relatório**: `report.md` (este arquivo)
- **Visualização**: [`{html_path}`]({html_path})
- **Gráfico Estático**: [`{png_path}`]({png_path})
- **Malha Original**: `{mesh_name}`
"""

    report_file = os.path.join(run_dir, "report.md")
    with open(report_file, 'w') as f:
        f.write(report_content)
        
    print(f"✓ Relatório gerado em: {report_file}")
    
    # Copiar para results/latest
    latest_dir = "results/latest"
    os.makedirs(latest_dir, exist_ok=True)
    shutil.copy(report_file, os.path.join(latest_dir, "report.md"))
    print(f"✓ Relatório disponível em: results/latest/report.md")

if __name__ == "__main__":
    generate_report()
