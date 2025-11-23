import argparse
import json
import os
import sys
from datetime import datetime

def load_registry(base_dir="checkpoints"):
    registry_path = os.path.join(base_dir, "registry.json")
    if not os.path.exists(registry_path):
        print(f"Erro: Registro não encontrado em {registry_path}")
        return {}
    try:
        with open(registry_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("Erro: Falha ao decodificar registry.json")
        return {}

def find_run(registry, problem_name=None, run_id=None):
    """Encontra o diretório de execução baseado no problema e run_id (ou o mais recente)."""
    if not registry:
        return None, None

    # Se não especificou problema, tenta adivinhar ou pega o primeiro
    if not problem_name:
        if len(registry) == 1:
            problem_name = list(registry.keys())[0]
        else:
            # Pega o problema com a execução mais recente
            latest_time = ""
            best_prob = None
            for prob, runs in registry.items():
                for run_data in runs.values():
                    if run_data["last_used"] > latest_time:
                        latest_time = run_data["last_used"]
                        best_prob = prob
            problem_name = best_prob

    if problem_name not in registry:
        print(f"Erro: Problema '{problem_name}' não encontrado no registro.")
        return None, None

    runs = registry[problem_name]
    
    selected_run = None
    selected_hash = None

    if run_id:
        # Busca por ID específico
        for h, data in runs.items():
            if data["run_id"] == run_id:
                selected_run = data
                selected_hash = h
                break
        if not selected_run:
            print(f"Erro: Run ID '{run_id}' não encontrado para o problema '{problem_name}'.")
            return None, None
    else:
        # Pega o mais recente
        latest_time = ""
        for h, data in runs.items():
            if data["last_used"] > latest_time:
                latest_time = data["last_used"]
                selected_run = data
                selected_hash = h

    return problem_name, selected_run

def generate_markdown_report(problem_name, run_data, metrics, run_dir):
    run_id = run_data["run_id"]
    config = run_data["config"]
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    md = f"# Relatório de Execução: {problem_name} - {run_id}\n\n"
    md += f"**Data do Relatório**: {date_str}\n"
    md += f"**Última Execução**: {run_data['last_used']}\n\n"
    
    md += "## 1. Configuração do Experimento\n\n"
    md += "| Parâmetro | Valor |\n"
    md += "|---|---|\n"
    for k, v in config.items():
        if k == "x0_list" or k == "train_box":
            v = str(v)
        md += f"| {k} | {v} |\n"
    md += "\n"
    
    md += "## 2. Métricas de Desempenho (MAE)\n\n"
    if metrics:
        # Ordenar métricas
        sorted_metrics = sorted(metrics.items(), key=lambda item: item[1])
        
        md += "| Modelo | MAE (Erro Médio Absoluto) | Diferença vs Melhor |\n"
        md += "|---|---|---|\n"
        
        best_mae = sorted_metrics[0][1]
        
        for model, mae in sorted_metrics:
            diff = f"+{(mae - best_mae):.6f}" if mae > best_mae else "🏆 Melhor"
            # Destaque para PINN
            model_fmt = f"**{model}**" if "PINN" in model else model
            md += f"| {model_fmt} | {mae:.6f} | {diff} |\n"
        
        md += "\n"
        
        # Análise Automática Simples
        pinn_mae = metrics.get("PINN")
        fem_mae = metrics.get("FEM")
        
        if pinn_mae and fem_mae:
            md += "### Análise Automática\n"
            if pinn_mae < fem_mae:
                improvement = (1 - pinn_mae/fem_mae) * 100
                md += f"> ✅ **Sucesso**: A PINN superou o Baseline Numérico (FEM) com um erro **{improvement:.1f}% menor**.\n"
            else:
                worsening = (pinn_mae/fem_mae - 1) * 100
                md += f"> ⚠️ **Atenção**: A PINN teve um erro **{worsening:.1f}% maior** que o Baseline Numérico (FEM).\n"
    else:
        md += "> ⚠️ Nenhuma métrica encontrada (metrics.json ausente).\n\n"

    md += "## 3. Visualizações\n\n"
    
    # Verifica imagens existentes
    images = {
        "Comparação Espacial": "comparison.png",
        "Extrapolação Temporal": "extrapolation.png",
        "Histórico de Loss": "loss_history.png" # Futuro
    }
    
    for title, filename in images.items():
        img_path = os.path.join(run_dir, filename)
        if os.path.exists(img_path):
            # Caminho relativo para o markdown funcionar se a pasta reports estiver no root
            # Mas como o report vai ser salvo em reports/, e as imagens estão em checkpoints/...,
            # precisamos do caminho relativo correto.
            # Reports dir: root/reports/
            # Images dir: root/checkpoints/prob/run/
            # Rel path: ../checkpoints/prob/run/filename
            
            rel_path = os.path.join("..", run_dir, filename)
            md += f"### {title}\n"
            md += f"![{title}]({rel_path})\n\n"

    return md

def main():
    parser = argparse.ArgumentParser(description="Gerador de Relatórios Automáticos para TCC")
    parser.add_argument("--problem", type=str, help="Nome do problema (ex: poisson_2d)")
    parser.add_argument("--run", type=str, help="ID da execução (ex: run_001)")
    parser.add_argument("--output_dir", type=str, default="reports", help="Diretório de saída para relatórios")
    
    args = parser.parse_args()
    
    # 1. Carregar Registro
    registry = load_registry()
    if not registry:
        return

    # 2. Encontrar Execução
    problem_name, run_data = find_run(registry, args.problem, args.run)
    
    if not run_data:
        print("Nenhuma execução encontrada.")
        return
        
    print(f"Gerando relatório para: {problem_name} - {run_data['run_id']}")
    
    # 3. Localizar Diretório e Métricas
    run_id = run_data["run_id"]
    run_dir = os.path.join("checkpoints", problem_name, run_id)
    metrics_path = os.path.join(run_dir, "metrics.json")
    
    metrics = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
    else:
        print(f"Aviso: metrics.json não encontrado em {run_dir}")

    # 4. Gerar Markdown
    report_md = generate_markdown_report(problem_name, run_data, metrics, run_dir)
    
    # 5. Salvar Relatório
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        
    report_filename = f"REPORT_{problem_name}_{run_id}.md"
    report_path = os.path.join(args.output_dir, report_filename)
    
    with open(report_path, 'w') as f:
        f.write(report_md)
        
    print(f"✅ Relatório gerado com sucesso: {report_path}")

if __name__ == "__main__":
    main()
