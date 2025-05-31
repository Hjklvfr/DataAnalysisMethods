import math
import re
import string

import pymorphy2
import requests
from bs4 import BeautifulSoup


ACCES_TOKEN = 'HDBXiZIdeWmlA6w34_KZ4evtpPanKAaXjXIAhX7GnAXqpY52gf79ZxcbR3e9avLE'


morph = pymorphy2.MorphAnalyzer()
class GeniusClient:

    def song_list(self, artist):
        url = f'https://genius.com/artists/{artist}'
        data = {'access_token': ACCES_TOKEN}

        response = requests.get(url, params=data)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            songs_elements = soup.find_all('div', class_='mini_card_grid-song')
            return list(map(lambda x: x.find('a')['href'], songs_elements))
        return []

    def get_lyrics(self, lyrics_link):
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; YourBot/0.1; +http://yourdomain.com/bot)"
        }

        try:
            page = requests.get(lyrics_link, headers=headers)
            page.raise_for_status()  # Проверка на успешный запрос
        except requests.RequestException as e:
            print(f"Ошибка при запросе страницы: {e}")
            return ""

        soup = BeautifulSoup(page.text, "html.parser")

        # Удаление всех тегов <script> и <style>, чтобы избавиться от лишнего контента
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Поиск всех блоков с текстом песни
        lyrics_blocks = soup.find_all('div', class_='Lyrics__Container-sc-1ynbvzw-1')

        if not lyrics_blocks:
            # Альтернативный способ поиска текста песни, если основной не сработал
            lyrics_div = soup.find("div", class_="lyrics")
            if lyrics_div:
                lyrics_text = lyrics_div.get_text(separator='\n')
                lines = lyrics_text.splitlines()
            else:
                print("Не удалось найти текст песни на странице.")
                return ""
        else:
            lyrics_text = []
            for block in lyrics_blocks:
                # Используем разделитель '\n' для сохранения переносов строк внутри блока
                block_text = block.get_text(separator='\n')
                lines = block_text.splitlines()
                for line in lines:
                    stripped_line = line.strip()
                    if stripped_line:  # Пропускаем пустые строки
                        lyrics_text.append(stripped_line + ' ')

            lyrics_text = '\n'.join(lyrics_text).splitlines()

        # Теперь удаляем все подстроки в квадратных скобках
        processed_lines = []
        for line in lines if not lyrics_blocks else lyrics_text:
            # Используем регулярное выражение для удаления текста в [ ]
            cleaned_line = re.sub(r'[.*?]', '', line).strip()
            if cleaned_line:  # Пропускаем пустые строки после очистки
                processed_lines.append(cleaned_line + ' ')

        # Соединяем обработанные строки с переносами
        return '\n'.join(processed_lines)


