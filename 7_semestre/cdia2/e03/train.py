from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from data_utils import gerar_dataset
from model_utils import (
    carregar_modelo,
    salvar_modelo,
    tamanho_arquivo_kb,
    validar_predicoes_iguais,
)


def executar_treino() -> None:
    df, x, y = gerar_dataset(n_samples=3000, seed=42, proporcao_positivos=0.12)

    print(df.head())
    print("\nDistribuição da classe:")
    print(df["fraude"].value_counts(normalize=True).round(4))

    print("\nMédias por classe:")
    print(
        df.groupby("fraude")[
            [
                "valor_transacao",
                "distancia_ultima_compra",
                "tentativas_senha",
                "device_risk_score",
            ]
        ]
        .mean()
        .round(2)
    )

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)
    print("\nClassification report:")
    print(classification_report(y_test, y_pred, target_names=["legitimo", "fraude"]))

    caminho_modelo = "model.pkl"
    salvar_modelo(model, caminho_modelo)
    tamanho_kb = tamanho_arquivo_kb(caminho_modelo)
    print(f"\nModelo salvo em {caminho_modelo} ({tamanho_kb:.1f} KB)")

    model_carregado = carregar_modelo(caminho_modelo)
    amostra = x_test[:5]
    pred_original = model.predict(amostra)
    pred_carregado = model_carregado.predict(amostra)
    validar_predicoes_iguais(pred_original, pred_carregado)

    print("Predicoes (modelo original):", pred_original)
    print("Predicoes (modelo carregado):", pred_carregado)


if __name__ == "__main__":
    executar_treino()