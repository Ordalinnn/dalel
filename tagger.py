"""Собственная модель разметки заданий по темам. Работает без ключа API и без интернета.

Модель: TF-IDF по буквенным n-граммам (2–5 символов) + логистическая регрессия.
Буквенные n-граммы подходят для казахского и русского: они ловят корни и окончания
(«теңсіздік», «неравенств», «пропорци») и не требуют словаря или лемматизатора.
Обучающие задания: data/train_items.csv. Отложенная проверка: data/test_items.csv
(эти задания модель при обучении не видит).
"""
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

DATA = Path(__file__).parent / "data"
REVIEW_BELOW = 0.45   # ниже этой уверенности задание уходит методисту на подтверждение


def _normalize(text):
    return str(text).lower().replace("ё", "е")


def train(train_df=None):
    df = train_df if train_df is not None else pd.read_csv(DATA / "train_items.csv")
    model = make_pipeline(
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, preprocessor=_normalize),
        LogisticRegression(max_iter=3000, C=10),
    )
    model.fit(df["text"], df["topic_code"])
    return model


def predict(model, text, plan, top=3):
    """Возвращает dict(topic_code, confidence, alternatives, reason, source)."""
    proba = model.predict_proba([text])[0]
    ranked = sorted(zip(model.classes_, proba), key=lambda x: -x[1])
    names = plan.set_index("topic_code")["topic_name"].to_dict()
    best, conf = ranked[0]
    alts = [(c, names.get(c, c), float(p)) for c, p in ranked[1:top]]
    reason = (f"Текст задания ближе всего к обучающим заданиям темы «{names.get(best, best)}». "
              f"Вторая по вероятности тема: «{alts[0][1]}» ({alts[0][2]:.2f}).")
    return {"topic_code": best, "confidence": float(conf), "alternatives": alts,
            "reason": reason, "source": "собственная модель (без API)"}


def evaluate(model=None):
    """Точность на отложенных заданиях, которых нет в обучении."""
    model = model or train()
    test = pd.read_csv(DATA / "test_items.csv")
    pred = model.predict(test["text"])
    proba = model.predict_proba(test["text"]).max(axis=1)
    test = test.assign(pred=pred, confidence=proba, ok=pred == test["topic_code"])
    return float(test["ok"].mean()), test


if __name__ == "__main__":
    acc, t = evaluate()
    print(f"Точность на {len(t)} отложенных заданиях: {acc:.0%}")
    for lang, g in t.groupby("lang"):
        print(f"  {lang}: {g['ok'].mean():.0%} ({g['ok'].sum()} из {len(g)})")
    print(t.loc[~t["ok"], ["text", "topic_code", "pred", "confidence"]].to_string())
    print("Уверенность: верные", round(t.loc[t.ok, "confidence"].mean(), 2),
          "ошибочные", round(t.loc[~t.ok, "confidence"].mean(), 2) if (~t.ok).any() else "-")
