import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Film:
    """Класс для хранения информации о фильме"""
    title: str
    original_title: str
    year: str
    rating: str
    genres: str
    country: str
    url: str
    director: str = ""  # Новое поле - режиссер


class KinoMailParser:

    def __init__(self):
        self.base_url = 'https://kino.mail.ru'
        self.top_url = f'{self.base_url}/cinema/top/'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': self.base_url,
            'DNT': '1'
        }
        self.delay = 2  # Задержка между запросами

    def _get_page(self, url: str) -> Optional[str]:
        """Получение HTML страницы с обработкой ошибок"""
        try:
            time.sleep(self.delay)
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Ошибка запроса {url}: {e}")
            return None

    def _parse_film_card(self, card) -> Optional[Film]:
        """Парсинг карточки фильма"""
        try:
            # Название фильма
            title_elem = card.select_one('span.link__text')
            if not title_elem:
                return None
            title = title_elem.text.strip()

            # Оригинальное название (может отсутствовать)
            original_title_elem = card.select_one('span.text_light_small.color_gray')
            original_title = original_title_elem.text.strip() if original_title_elem else ""

            # Детали (страна, год, жанры)
            details = card.select('div.margin_top_5 a')
            country = details[0].text.strip() if len(details) > 0 else ""
            year = details[1].text.strip() if len(details) > 1 else ""
            genres = ', '.join([g.text.strip() for g in details[2:]]) if len(details) > 2 else ""

            # Рейтинг
            rating_elem = card.select_one('span.p-rate-flag__text')
            rating = rating_elem.text.strip() if rating_elem else "Н/Д"

            # Ссылка
            url_elem = card.select_one('a.link-holder_itemevent_small')
            if not url_elem or 'href' not in url_elem.attrs:
                return None
            url = self.base_url + url_elem['href']

            return Film(
                title=title,
                original_title=original_title,
                year=year,
                rating=rating,
                genres=genres,
                country=country,
                url=url
            )
        except Exception as e:
            print(f"Ошибка парсинга карточки фильма: str{e}")
            return None

    def get_top_films(self, count: int = 50) -> List[Film]:

        if count < 1 or count > 150:
            raise ValueError("Можно собрать от 1 до 150 фильмов")

        films = []
        page = 1

        while len(films) < count:
            url = f"{self.top_url}?page={page}" if page > 1 else self.top_url
            html = self._get_page(url)

            if not html:
                break

            soup = BeautifulSoup(html, 'lxml')
            cards = soup.select('div.p-itemevent-small')

            if not cards:
                break

            for card in cards:
                film = self._parse_film_card(card)
                if film:
                    films.append(film)
                    if len(films) >= count:
                        break

            page += 1

        return films[:count]

    def save_to_json(self, films: List[Film], filename: str):
        """Сохранение в JSON файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([vars(f) for f in films], f, ensure_ascii=False, indent=2)
        print(f"Данные сохранены в {filename}")

    def save_to_csv(self, films: List[Film], filename: str):
        """Сохранение в CSV файл"""
        pd.DataFrame([vars(f) for f in films]).to_csv(filename, index=False)
        print(f"Данные сохранены в {filename}")

    def save_to_excel(self, films: List[Film], filename: str):
        """Сохранение в Excel файл"""
        pd.DataFrame([vars(f) for f in films]).to_excel(filename, index=False)
        print(f"Данные сохранены в {filename}")


if __name__ == "__main__":
    # Пример использования
    parser = KinoMailParser()

    print("=== Парсер топ-фильмов с kino.mail.ru ===")
    print("Можно собрать от 1 до 150 фильмов")

    try:
        count = int(input("Сколько фильмов собрать (1-150)? "))
        if count < 1 or count > 150:
            raise ValueError
    except ValueError:
        print("Ошибка: введите число от 1 до 150")
        exit()

    print(f"\nСбор топ-{count} фильмов...")
    films = parser.get_top_films(count)

    if not films:
        print("Не удалось собрать данные. Попробуйте позже.")
    else:
        print(f"\nУспешно собрано {len(films)} фильмов")

        # Сохранение во всех форматах
        base_filename = f"kino_mail_top_{count}_films"

        parser.save_to_json(films, f"{base_filename}.json")
        parser.save_to_csv(films, f"{base_filename}.csv")
        parser.save_to_excel(films, f"{base_filename}.xlsx")
