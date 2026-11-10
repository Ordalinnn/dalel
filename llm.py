"""Работа с языковой моделью: разметка заданий и записка.

Ключ берётся из секретов Streamlit или переменных окружения:
  ANTHROPIC_API_KEY  (модель задаётся ANTHROPIC_MODEL)
  или OPENAI_API_KEY (модель задаётся OPENAI_MODEL)
Без ключа приложение работает в резервном режиме: разметка из кэша, записка по шаблону.
"""
import json
import os

import requests

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5-5"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"


def _secret(name):
    try:
        import streamlit as st
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name)


def provider():
    if _secret("ANTHROPIC_API_KEY"):
        return "anthropic"
    if _secret("OPENAI_API_KEY"):
        return "openai"
    return None


def _call(system, user, max_tokens=900):
    p = provider()
    if p == "anthropic":
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": _secret("ANTHROPIC_API_KEY"), "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": _secret("ANTHROPIC_MODEL") or DEFAULT_ANTHROPIC_MODEL, "max_tokens": max_tokens,
                  "temperature": 0, "system": system, "messages": [{"role": "user", "content": user}]},
            timeout=60,
        )
        r.raise_for_status()
        return "".join(b.get("text", "") for b in r.json()["content"])
    if p == "openai":
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {_secret('OPENAI_API_KEY')}"},
            json={"model": _secret("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL, "temperature": 0,
                  "max_tokens": max_tokens,
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    raise RuntimeError("Ключ API не задан")


def _parse_json(text):
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1])


# ---------- разметка заданий ----------

TAG_SYSTEM = (
    "Ты методист по математике в школе Казахстана. Тебе дают текст задания и закрытый список тем "
    "учебной программы. Выбери ОДНУ тему, которую проверяет задание. Выбирать можно только код из списка. "
    "Если задание не подходит ни к одной теме, верни код NONE. "
    'Ответь только JSON: {"topic_code": "...", "confidence": число от 0 до 1, "reason": "одно короткое предложение по-русски"}'
)


def tag_item(text, plan):
    """Возвращает dict(topic_code, confidence, reason, source). Код всегда из закрытого списка или NONE."""
    topics = "\n".join(f"{r.topic_code}: {r.topic_name}" for r in plan.itertuples())
    allowed = set(plan["topic_code"]) | {"NONE"}
    out = _parse_json(_call(TAG_SYSTEM, f"Темы:\n{topics}\n\nЗадание:\n{text}", max_tokens=200))
    code = str(out.get("topic_code", "NONE")).strip()
    if code not in allowed:
        code, conf = "NONE", 0.0
    else:
        conf = float(out.get("confidence", 0))
    return {"topic_code": code, "confidence": max(0.0, min(1.0, conf)),
            "reason": str(out.get("reason", "")), "source": "модель"}


# Резерв для демо без интернета: заранее размеченные примеры (проверены вручную).
CACHED_TAGS = {
    "Поезд прошёл 240 км за 3 часа. Сколько километров он пройдёт за 5 часов с той же скоростью?":
        {"topic_code": "Т01", "confidence": 0.93, "reason": "Задача на прямую пропорциональную зависимость."},
    "Решите неравенство: 5 - 2x ≤ 11.":
        {"topic_code": "Т07", "confidence": 0.97, "reason": "Нужно решить линейное неравенство."},
    "Постройте на координатной плоскости точки A(-2; 3) и B(4; -1) и найдите координаты точки пересечения отрезка AB с осью ординат.":
        {"topic_code": "Т08", "confidence": 0.82, "reason": "Работа с точками на координатной плоскости."},
}


# ---------- записка ----------

MEMO_SYSTEM = (
    "Ты пишешь аналитическую записку для районного методического совета. Тебе дают таблицу фактов в JSON. "
    "Для казахского текста бери названия тем из поля topic_kk. "
    "Правила: 1) Используй ТОЛЬКО числа из таблицы фактов, ничего не вычисляй и не округляй заново. "
    "2) Не придумывай новых фактов, причин и названий. 3) Если различие помечено confirmed=false, "
    "пиши, что различие не подтверждено. 4) Рекомендации по часам называй предложением для пилота. "
    "5) Стиль деловой, без вступлений и восклицаний, 180–260 слов. Структура: краткий вывод; "
    "слабые темы и причины; сравнение учебников; предложения по часам. "
    "6) Номера разделов и маркеры списков не пиши цифрами: используй тире."
)

LANG_NAME = {"ru": "на русском языке", "kk": "на казахском языке"}


def write_memo(facts, lang):
    return _call(MEMO_SYSTEM, f"Напиши записку {LANG_NAME[lang]}.\n\nТаблица фактов:\n"
                              f"{json.dumps(facts, ensure_ascii=False, indent=1)}", max_tokens=1200)


def template_memo(facts, lang):
    """Записка по шаблону, без модели. Используется, если ключа нет или сеть недоступна."""
    f = facts
    if lang == "kk":
        out = [f"{f['subject']}. Талдауға {f['n_schools']} мектептің {f['n_students']} оқушысының нәтижесі алынды. "
               f"Мақсатты меңгеру деңгейі – {f['target_pct']}%."]
        cause_kk = {"topic": "тақырыптың өзі қиын", "textbook": "оқулыққа қатысты мәселе",
                    "schools": "жекелеген мектептер артта қалып отыр", "item": "тапсырма сапасыз",
                    "nodata": "дерек жеткіліксіз"}
        if f["weak_topics"]:
            out.append("Мақсаттан төмен меңгерілген тақырыптар:")
            for w in f["weak_topics"]:
                line = f"– «{w['topic_kk']}»: {w['mastery_pct']}% ({w['ci_low_pct']}–{w['ci_high_pct']}%), себебі: {cause_kk[w['cause']]}"
                if w["cause"] == "textbook":
                    line += f" («{w['textbook']}» бойынша {w['gap_pp']} п.т. төмен)"
                out.append(line + ".")
        tb = sorted(f["textbooks_adjusted"], key=lambda x: -x["mean_pct"])
        out.append("Түзетуден кейінгі оқулықтар нәтижесі: " +
                   "; ".join(f"«{t['textbook']}» – {t['mean_pct']}%" for t in tb) + ".")
        if f["hours"]:
            out.append("Сағаттарды қайта бөлу ұсынысы (пилотқа арналған болжам, жалпы сағат саны "
                       f"{f['total_hours']} өзгермейді):")
            for h in f["hours"]:
                verb = "қосу" if h["direction"] == "добавить" else "қысқарту"
                out.append(f"– «{h['topic_kk']}»: {h['old']} → {h['new']} сағат ({h['delta']} сағат {verb}).")
        return "\n".join(out)

    out = [f"{f['subject']}. В анализ вошли результаты {f['n_students']} учеников из {f['n_schools']} школ. "
           f"Целевой уровень освоения темы: {f['target_pct']}%."]
    if f["weak_topics"]:
        out.append("Темы ниже целевого уровня:")
        for w in f["weak_topics"]:
            line = (f"– «{w['topic']}»: {w['mastery_pct']}% (интервал {w['ci_low_pct']}–{w['ci_high_pct']}%). "
                    f"Причина: {w['cause_title'].lower()}")
            if w["cause"] == "textbook":
                line += f", с учебником «{w['textbook']}» тема усвоена на {w['gap_pp']} п.п. хуже"
            if w["cause"] == "schools":
                line += f" (школ: {w['schools_count']})"
            out.append(line + f". Действие: {w['action']}")
    tb = sorted(f["textbooks_adjusted"], key=lambda x: -x["mean_pct"])
    out.append("Результаты по учебникам с поправкой на прошлый балл, тип местности и язык обучения: " +
               "; ".join(f"«{t['textbook']}» {t['mean_pct']}%" for t in tb) + ".")
    for pr in f["textbook_pairs"]:
        status = "различие подтверждено" if pr["confirmed"] else "различие не подтверждено"
        out.append(f"– «{pr['a']}» и «{pr['b']}»: разница {pr['diff_pp']} п.п. в пользу «{pr['better']}», {status}.")
    if f["hours"]:
        out.append(f"Предложение для пилота по часам (общее число часов {f['total_hours']} не меняется):")
        for h in f["hours"]:
            out.append(f"– «{h['topic']}»: {h['old']} → {h['new']} ч ({h['direction']} {h['delta']} ч).")
    out.append("Выводы основаны на наблюдательных данных и требуют проверки в пилоте.")
    return "\n".join(out)
