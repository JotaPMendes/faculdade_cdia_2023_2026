# 🧠 Aprendizados e Melhores Práticas (DeepXDE & PINNs)

Este documento centraliza os aprendizados técnicos adquiridos durante o desenvolvimento deste projeto, focando especialmente na resolução de problemas eletrostáticos com geometrias complexas usando DeepXDE.

## 1. O Desafio das Geometrias Complexas
Em geometrias não-triviais (como o Estator do Motor ou Domínio em L), as PINNs "vanilla" tendem a falhar nas bordas.
**Sintoma:** A solução fica suave no centro (onde o Laplaciano é zero), mas não respeita os valores de potencial nas bordas (0V ou 100V), resultando em um "borrão".

### 🔧 Soluções Aplicadas

#### A. Pesos de Fronteira (Loss Weighting) ⚖️
A função de perda (Loss) é uma soma ponderada:
$$ Loss = w_{PDE} \cdot Loss_{PDE} + w_{BC} \cdot Loss_{BC} $$

*   **Problema:** Se $w_{BC} = 1.0$, a rede pode achar "mais barato" minimizar o PDE no interior do que acertar a borda complexa.
*   **Solução:** Aumentar drasticamente o peso das BCs.
*   **Implementação:** Definimos `loss_weights = [1.0, 100.0, ...]` no `models/pinn.py`. Isso força a rede a priorizar as condições de contorno.

#### B. Densidade de Pontos (Sampling) 📍
*   **Problema:** Com poucos pontos (ex: 5000), detalhes finos como os "dentes" do estator ficam sub-representados.
*   **Solução:** Aumentar a densidade global e usar reamostragem.
*   **Implementação:**
    1.  Aumentamos `N_data` para **10.000** em `config.py`.
    2.  Utilizamos `dde.callbacks.PDEPointResampler(period=1000)`, que a cada 1000 épocas adiciona pontos onde o erro residual é maior (Adaptive Sampling).

#### C. Singularidades (Cantos Vivos) 📐
Cantos de 90º (L-Shape) ou pontas afiadas geram campos elétricos teoricamente infinitos.
*   **Aprendizado:** Redes neurais (funções contínuas) têm dificuldade em aproximar descontinuidades.
*   **Mitigação:** O *Adaptive Sampling* ajuda a concentrar esforço nessas regiões. Em casos extremos, pode-se usar *Singularity Enrichment* (adicionar termo analítico à rede), mas por enquanto a força bruta (mais pontos + pesos) tem sido suficiente.

## 2. Pipeline de Visualização "Geometry-Aware"
Visualizar a saída da PINN em um grid retangular (`np.meshgrid`) gera artefatos "denteados" nas bordas curvas.
*   **Solução:** Usar a própria malha de elementos finitos (`.msh`) para plotagem.
*   **Ferramenta:** `plotly.graph_objects.Mesh3d`.
*   **Vantagem:** O gráfico respeita exatamente os furos e curvas da geometria, permitindo uma validação visual precisa "dentro" da peça.

## 3. Estrutura de Projeto para Avaliação
Para facilitar a reprodutibilidade e avaliação:
*   **Centralização:** Todos os resultados finais são copiados para `results/latest/`.
*   **Configuração Dinâmica:** O arquivo `config.py` controla tudo (malha, física, hiperparâmetros), evitando "hardcoding" espalhado.
*   **Modularidade:** A lógica de malha (`electrostatic_mesh.py`) é desacoplada da lógica de treino (`pinn.py`), permitindo trocar geometrias apenas mudando o arquivo `.msh`.

## 4. Referências e Leitura
*   **DeepXDE Docs:** Adaptive Loss Weights.
*   **Literatura:** "Physics-Informed Neural Networks for Complex Geometries".
