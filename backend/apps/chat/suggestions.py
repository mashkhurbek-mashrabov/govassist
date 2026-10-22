"""Curated starter questions per UI language (questions only, no facts)."""

from apps.common.i18n import Lang

MAX_SUGGESTIONS = 6

SUGGESTIONS: dict[str, list[tuple[str, str]]] = {
    Lang.UZ_LATN: [
        ("Pasportimni qanday almashtiraman?", "passport"),
        ("Tugʻilganlik haqidagi guvohnomani qanday olaman?", "civil_registry"),
        ("Nikohni qayerda roʻyxatdan oʻtkazish mumkin?", "civil_registry"),
        ("Yashash joyi boʻyicha roʻyxatdan qanday oʻtaman?", "registration"),
        ("Haydovchilik guvohnomasini qanday almashtiraman?", "transport"),
        ("Mehnat shartnomasi qanday tuziladi?", "labor"),
    ],
    Lang.UZ_CYRL: [
        ("Паспортимни қандай алмаштираман?", "passport"),
        ("Туғилганлик ҳақидаги гувоҳномани қандай оламан?", "civil_registry"),
        ("Никоҳни қаерда рўйхатдан ўтказиш мумкин?", "civil_registry"),
        ("Яшаш жойи бўйича рўйхатдан қандай ўтаман?", "registration"),
        ("Ҳайдовчилик гувоҳномасини қандай алмаштираман?", "transport"),
        ("Меҳнат шартномаси қандай тузилади?", "labor"),
    ],
    Lang.RU: [
        ("Как заменить паспорт?", "passport"),
        ("Как получить свидетельство о рождении?", "civil_registry"),
        ("Где зарегистрировать брак?", "civil_registry"),
        ("Как встать на учёт по месту жительства?", "registration"),
        ("Как заменить водительское удостоверение?", "transport"),
        ("Как оформляется трудовой договор?", "labor"),
    ],
    Lang.EN: [
        ("How do I replace my passport?", "passport"),
        ("How do I get a birth certificate?", "civil_registry"),
        ("Where can I register a marriage?", "civil_registry"),
        ("How do I register my place of residence?", "registration"),
        ("How do I replace my driving licence?", "transport"),
        ("How is an employment contract concluded?", "labor"),
    ],
}


def suggestions_for(lang: str) -> list[dict[str, str]]:
    """At most six starter questions in ``lang``.

    Args:
        lang: A ``Lang`` value.
    """
    items = SUGGESTIONS.get(lang, SUGGESTIONS[Lang.UZ_LATN])[:MAX_SUGGESTIONS]
    return [{"text": text, "category": category} for text, category in items]
