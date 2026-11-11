"""Библиотека «Дәлел»: что почитать учителю при каждом диагнозе темы.

Ключи BOOKS совпадают с ключами core.CAUSES. Для «nodata» книг нет: там нужен не совет, а данные.
Названия книг даются на русском; если русского издания нет, english=True.
"""

WHY = {
    "topic": ("как разбирать трудную задачу по шагам и строить понимание",
              "қиын есепті қадам бойынша талдау және түсінікті қалыптастыру"),
    "textbook": ("приёмы урока: объяснение, проверка понимания, темп",
                 "сабақ тәсілдері: түсіндіру, түсінуді тексеру, қарқын"),
    "schools": ("какие меры реально работают и как оценивать по ходу урока",
                "қандай шаралар шынымен нәтиже береді және сабақ барысында қалай бағалау керек"),
    "item": ("как составить задание, которое различает сильных и слабых",
             "күшті және әлсіз оқушыларды ажырататын тапсырманы қалай құрастыру керек"),
}


def _book(cause, author, title_ru, title_original, english=False):
    why_ru, why_kk = WHY[cause]
    return {"author": author, "title_ru": title_ru, "title_original": title_original,
            "why_ru": why_ru, "why_kk": why_kk, "english": english}


BOOKS = {
    "topic": [
        _book("topic", "Д. Пойа", "Как решать задачу", "How to Solve It"),
        _book("topic", "Джо Боулер", "Математическое мышление", "Mathematical Mindsets"),
    ],
    "textbook": [
        _book("textbook", "Дуг Лемов", "Мастерство учителя", "Teach Like a Champion"),
    ],
    "schools": [
        _book("schools", "Джон Хэтти", "Видимое обучение", "Visible Learning"),
        _book("schools", "Дилан Уильям", "Embedded Formative Assessment", "Embedded Formative Assessment",
              english=True),
    ],
    "item": [
        _book("item", "В. С. Аванесов", "Композиция тестовых заданий", "Композиция тестовых заданий"),
    ],
}

# Кому какие диагнозы ближе: учитель меняет урок, завуч работает со школой, методист — с программой и тестом.
ROLES = {
    "Методист": ["item", "topic", "schools"],
    "Завуч": ["schools", "textbook"],
    "Учитель": ["topic", "textbook"],
}


def books_for(cause):
    """Книги для диагноза; для неизвестной причины или «nodata» — пустой список."""
    return BOOKS.get(cause, [])


def title_line(book):
    """«Автор. Название» и, если название переводное, оригинал в скобках."""
    line = f"{book['author']}. «{book['title_ru']}»"
    if book["english"]:
        line += " (издание на английском)"
    elif book["title_original"] != book["title_ru"]:
        line += f" ({book['title_original']})"
    return line
