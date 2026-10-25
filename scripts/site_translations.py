"""Build an English copy of the dependency-free browser script."""
APP_EN = {
    'Включить светлую тему': 'Switch to light theme', 'Включить тёмную тему': 'Switch to dark theme',
    'Светлая':'Light', 'Тёмная':'Dark', 'Найдено проектов:':'Projects found:',
    'Ничего не найдено. Попробуйте другое название или категорию.':'No projects found. Try another name or category.',
    'Дата не указана':'Date unavailable', 'Подробности этого выпуска доступны на GitHub.':'Release details are available on GitHub.',
    'Что изменилось':"What's new", 'Описание выпуска не заполнено.':'No release description was provided.',
    'Полный выпуск на GitHub ↗':'Full release on GitHub ↗', 'device-tools · инструменты iPhone':'device-tools · iPhone tools',
    'Стабильный выпуск':'Stable release', 'Выпущено':'Released', 'Предварительный выпуск:':'Preview release:',
    'для тестирования':'for testing', 'История выпусков':'Release history', 'предварительный':'preview',
    'Скачать device-tools ↓':'Download device-tools ↓', 'Открыть выпуск device-tools ↗':'Open device-tools release ↗',
    'Открыть страницу выпуска':'Open release page', 'Скачать':'Download', 'Предварительный':'Preview', 'Стабильный':'Stable',
    'Для выбранного проекта пока нет выпусков в ленте.':'No releases for this project are currently in the feed.',
    'Данные GitHub Releases проверены':'GitHub Releases checked on', 'МСК':'MSK',
    'Время проверки неизвестно.':'The last check time is unavailable.',
    'Показываем последние сохранённые данные; обновление временно задерживается.':'Showing the last saved data; updates are temporarily delayed.',
    'Обновление примерно раз в час.':'Updates approximately once an hour.',
    'Не удалось загрузить версии. Актуальные выпуски доступны по ссылкам на GitHub.':'Could not load versions. Current releases are available on GitHub.',
    'Язык не указан':'Language not specified', 'форк':'fork', 'проект':'project', 'архив':'archived',
    'Описание пока не добавлено на GitHub.':'No description has been added on GitHub.', 'Последний коммит:':'Last commit:',
    ' на GitHub':' on GitHub', 'Других публичных репозиториев пока нет.':'No other public repositories yet.',
    'Каталог GitHub проверен':'GitHub catalog checked on',
    'Показываем последний сохранённый список; обновление задерживается.':'Showing the last saved catalog; updates are delayed.',
    'Новые публичные репозитории появляются автоматически, примерно раз в час.':'New public repositories appear automatically, approximately once an hour.',
    'Показываем сохранённый каталог. Список репозиториев доступен на GitHub.':'Showing the saved catalog. The repository list is available on GitHub.',
}


def translate_app(source):
    source = source.replace("'ru-RU'", "'en-GB'").replace("'ru'", "'en'")
    for ru in sorted(APP_EN, key=len, reverse=True):
        # Replacement strings are inserted into JS single-quoted strings and template literals.
        source = source.replace(ru, APP_EN[ru].replace("'", "\\'"))
    return source
