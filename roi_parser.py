#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер сайта roi.ru - Федеральные инициативы
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime
import logging
from urllib.parse import urljoin, urlparse, parse_qs
import json

class ROIParser:
    def __init__(self):
        self.base_url = "https://www.roi.ru"
        self.federal_url = "https://www.roi.ru/poll/last/?level=1"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/parser.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def parse_federal_initiatives(self, start_url=None, max_pages=3):
        """
        Парсинг федеральных инициатив с сайта roi.ru
        Args:
            start_url: начальный URL для парсинга (если None, используем self.federal_url)
            max_pages: максимальное количество страниц для парсинга
        Returns:
            list: список инициатив
        """
        all_initiatives = []
        
        try:
            # Парсим первую страницу
            current_page = 1
            current_url = start_url if start_url else self.federal_url
            
            while current_page <= max_pages and current_url:
                self.logger.info(f"Парсинг страницы {current_page}: {current_url}")
                
                # Получаем HTML страницы
                response = self.session.get(current_url, timeout=30)
                response.raise_for_status()
                
                # Парсим HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Извлекаем инициативы с текущей страницы
                page_initiatives = self._parse_initiatives_page(soup)
                all_initiatives.extend(page_initiatives)
                
                self.logger.info(f"Страница {current_page}: найдено {len(page_initiatives)} инициатив")
                
                # Находим ссылку на следующую страницу
                next_url = self._get_next_page_url(soup, current_url)
                
                if next_url and next_url != current_url:
                    current_url = next_url
                    current_page += 1
                    
                    # Задержка между запросами, чтобы не нагружать сервер
                    time.sleep(2)
                else:
                    self.logger.info(f"Достигнут конец пагинации или следующая страница не найдена")
                    break
                    
        except Exception as e:
            self.logger.error(f"Ошибка при парсинге федеральных инициатив: {e}")
            import traceback
            traceback.print_exc()
        
        self.logger.info(f"Всего распарсено федеральных инициатив: {len(all_initiatives)}")
        return all_initiatives
    
    def _parse_initiatives_page(self, soup):
        """
        Парсинг страницы со списком инициатив
        """
        initiatives = []
        
        # Ищем блоки с инициативами
        # Из HTML видно, что инициативы находятся в div с классами 'col-1' и 'col-2'
        initiative_blocks = soup.find_all('div', class_=['col-1', 'col-2'])
        
        if not initiative_blocks:
            # Альтернативный поиск: ищем div с классом 'item'
            initiative_blocks = soup.find_all('div', class_='item')
        
        for block in initiative_blocks:
            try:
                initiative = self._parse_initiative_block(block)
                if initiative:
                    initiatives.append(initiative)
            except Exception as e:
                self.logger.error(f"Ошибка парсинга блока инициативы: {e}")
                continue
        
        return initiatives
    
    def _parse_initiative_block(self, block):
        """
        Парсинг блока отдельной инициативы
        """
        try:
            # 1. Извлекаем ID и URL
            link_elem = block.find('div', class_='link').find('a') if block.find('div', class_='link') else None
            if not link_elem:
                return None
            
            href = link_elem.get('href', '')
            url = urljoin(self.base_url, href)
            
            # Извлекаем ID из URL (например, /134431/ -> 134431)
            initiative_id = self._extract_id_from_url(url)
            
            # 2. Извлекаем заголовок
            title = link_elem.get_text(strip=True)
            
            # 3. Извлекаем количество голосов ЗА
            votes_text = "0"
            votes_elem = block.find('div', class_='hour')
            if votes_elem:
                # Ищем тег <b> с числом голосов
                b_tag = votes_elem.find('b')
                if b_tag:
                    votes_text = b_tag.get_text(strip=True).replace(' ', '')
            
            # 4. Извлекаем уровень инициативы
            level = "Федеральный"
            jurisdiction_elem = block.find('div', class_='jurisdiction')
            if jurisdiction_elem:
                level_text = jurisdiction_elem.get_text(strip=True)
                if 'Уровень инициативы:' in level_text:
                    level = level_text.replace('Уровень инициативы:', '').strip()
            
            # 5. Извлекаем категорию (если есть)
            category = "Не указана"
            # Можно добавить поиск категории, если она есть в блоке
            
            # 6. Извлекаем дату (используем текущую дату, так как на странице ее нет)
            created_date = datetime.now().strftime('%Y-%m-%d')
            
            # 7. Формируем описание (используем заголовок как краткое описание)
            description = f"{title}. Количество голосов: {votes_text}"
            
            return {
                'external_id': initiative_id,
                'title': title,
                'description': description,
                'url': url,
                'category': category,
                'level': level,
                'votes': votes_text,          # Голоса ЗА из списка
                'anti_votes': '0',            # Голоса ПРОТИВ (будет уточнено на детальной странице)
                'created_date': created_date,
                'parsed_at': datetime.now().isoformat(),
                'source': 'roi.ru'
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка парсинга блока: {e}")
            return None
    
    def _extract_id_from_url(self, url):
        """Извлечение ID из URL"""
        # Пример URL: https://www.roi.ru/134431/
        # Или: /134431/
        match = re.search(r'/(\d+)/?$', url)
        if match:
            return f"roi_{match.group(1)}"
        
        # Если не нашли, генерируем хэш
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"roi_{url_hash}"
    
    def _get_next_page_url(self, soup, current_url):
        """Получение URL следующей страницы"""
        try:
            # Пробуем разные варианты поиска пагинации
            # Вариант 1: ищем по классу 'pagination'
            pagination = soup.find('div', class_='pagination')
            
            # Если не нашли, пробуем 'yiiPager'
            if not pagination:
                pagination = soup.find('div', class_='yiiPager')
            
            # Если все еще не нашли, ищем по любому div с классом содержащим 'pagination'
            if not pagination:
                for div in soup.find_all('div'):
                    classes = div.get('class', [])
                    if classes and ('pagination' in classes or 'yiiPager' in classes):
                        pagination = div
                        break
            
            self.logger.info(f"Поиск пагинации. Найден элемент: {pagination is not None}")
            
            if not pagination:
                self.logger.warning("Пагинация не найдена!")
                return None
            
            self.logger.info(f"Классы пагинации: {pagination.get('class', [])}")
            
            # Ищем ссылку с классом 'next'
            next_link = pagination.find('a', class_='next')
            
            # Если не нашли, ищем ссылку с текстом "Следующая"
            if not next_link:
                for a in pagination.find_all('a'):
                    if 'Следующая' in a.get_text():
                        next_link = a
                        break
            
            self.logger.info(f"Найдена ссылка 'next': {next_link is not None}")
            
            if next_link and next_link.get('href'):
                href = next_link['href']
                next_url = urljoin(self.base_url, href)
                self.logger.info(f"Сформирован URL следующей страницы: {next_url}")
                return next_url
            else:
                self.logger.warning("Ссылка на следующую страницу не найдена или без href")
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка при поиске следующей страницы: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def parse_initiative_details(self, url):
        """
        Парсинг детальной страницы инициативы
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Сохраним HTML для отладки
            # with open('debug_page.html', 'w', encoding='utf-8') as f:
            #     f.write(response.text)
            # self.logger.info("HTML страницы сохранен в debug_page.html")

            soup = BeautifulSoup(response.content, 'html.parser')
            
            details = {
                'full_text': '',
                'proposal_text': '',
                'result_text': '',
                'end_date': '',
                'author': '',
                'status': 'на голосовании',
                'votes': '0',
                'anti_votes': '0',
                'views': '0',
                'comments': '0'
            }
            
            # 1. Ищем основной блок с текстом инициативы
            # В HTML видно, что текст в блоке с классом 'block petition-text-block'
            text_block = soup.find('div', class_='block petition-text-block')
            if text_block:
                # Ищем все параграфы внутри этого блока
                paragraphs = text_block.find_all('p')
                if paragraphs:
                    full_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
                    if full_text:
                        details['full_text'] = full_text[:5000]  # Ограничиваем длину
                else:
                    # Если нет <p>, ищем текстовые узлы напрямую
                    text_elements = text_block.find_all('div', class_='paragraph-transform')
                    if text_elements:
                        full_text = ' '.join([elem.get_text(strip=True) for elem in text_elements])
                        if full_text:
                            details['full_text'] = full_text[:5000]
            
            # 2. Ищем "Практический результат"
            # Ищем заголовок h2 с текстом "Практический результат"
            for h2 in soup.find_all('h2'):
                if h2.get_text(strip=True) == 'Практический результат':
                    # Ищем следующий элемент с текстом
                    next_elem = h2.find_next('div', class_='paragraph-transform')
                    if next_elem:
                        details['result_text'] = next_elem.get_text(strip=True)
                    break
            
            # 3. Ищем "Решение"
            for h2 in soup.find_all('h2'):
                if h2.get_text(strip=True) == 'Решение':
                    # Ищем все блоки решений
                    decision_items = h2.find_next('div', class_='decision-item')
                    if decision_items:
                        decision_texts = []
                        # Ищем все параграфы в блоке решения
                        decision_paragraphs = decision_items.find_all('div', class_='paragraph-transform')
                        for p in decision_paragraphs:
                            decision_texts.append(p.get_text(strip=True))
                        
                        if decision_texts:
                            details['proposal_text'] = '\n'.join(decision_texts)
                    break
            
            # 4. Ищем дату окончания голосования в правой колонке
            aside_block = soup.find('aside', class_='col-right')
            if aside_block:
                # Ищем блок с классом 'inic-side-info'
                side_info = aside_block.find('div', class_='inic-side-info')
                if side_info:
                    # Ищем заголовок "Голосование закончится"
                    for div in side_info.find_all('div', class_='title'):
                        if 'Голосование закончится' in div.get_text():
                            # Следующий div с классом 'date' содержит дату
                            date_div = div.find_next('div', class_='date')
                            if date_div:
                                date_text = date_div.get_text(strip=True)
                                try:
                                    # Пробуем разные форматы даты
                                    for fmt in ['%d-%m-%Y', '%Y-%m-%d', '%d.%m.%Y']:
                                        try:
                                            end_date = datetime.strptime(date_text, fmt).strftime('%Y-%m-%d')
                                            details['end_date'] = end_date
                                            break
                                        except:
                                            continue
                                except:
                                    details['end_date'] = date_text
            
            # 5. Ищем автора
            author_div = soup.find('div', class_='author')
            if author_div:
                author_text = author_div.get_text(strip=True)
                details['author'] = author_text
            
            # 7. Ищем голоса ЗА и ПРОТИВ в правой колонке
            aside_block = soup.find('aside', class_='col-right')
            if aside_block:
                # Ищем блок с информацией об инициативе
                inic_info = aside_block.find('div', class_='inic-side-info')
                if inic_info:
                    # Ищем голоса ЗА
                    for div in inic_info.find_all('div', class_='voting-solution'):
                        # Проверяем текст внутри div
                        div_text = div.get_text(strip=True)
                        
                        # Голоса ЗА
                        if 'За инициативу подано:' in div_text:
                            vote_elem = div.find('b', class_='js-voting-info-affirmative')
                            if vote_elem:
                                votes_text = vote_elem.get_text(strip=True)
                                # Извлекаем только цифры
                                votes_num = ''.join(filter(str.isdigit, votes_text))
                                details['votes'] = votes_num if votes_num else '0'
                        
                        # Голоса ПРОТИВ
                        elif 'Против инициативы подано:' in div_text:
                            vote_elem = div.find('b', class_='js-voting-info-negative')
                            if vote_elem:
                                anti_votes_text = vote_elem.get_text(strip=True)
                                # Извлекаем только цифры
                                anti_votes_num = ''.join(filter(str.isdigit, anti_votes_text))
                                details['anti_votes'] = anti_votes_num if anti_votes_num else '0'
            
            # Альтернативный поиск голосов ПРОТИВ в основном блоке
            if details['anti_votes'] == '0':
                # Ищем блок с классом 'voting-solution' и текстом "Против"
                for div in soup.find_all('div', class_='voting-solution'):
                    if 'Против инициативы подано:' in div.get_text():
                        negative_elem = div.find('b', class_='js-voting-info-negative')
                        if negative_elem:
                            anti_votes_text = negative_elem.get_text(strip=True)
                            anti_votes_num = ''.join(filter(str.isdigit, anti_votes_text))
                            details['anti_votes'] = anti_votes_num if anti_votes_num else '0'
                        break
            
            # 8. Также обновим голоса ЗА из списка, если они есть
            if details['votes'] == '0':
                # Ищем голоса в основном блоке
                vote_elem = soup.find('b', class_='js-voting-info-affirmative')
                if vote_elem:
                    votes_text = vote_elem.get_text(strip=True)
                    votes_num = ''.join(filter(str.isdigit, votes_text))
                    details['votes'] = votes_num if votes_num else '0'
            
            self.logger.info(f"Для URL {url}:")
            self.logger.info(f"  Голоса ЗА: {details['votes']}")
            self.logger.info(f"  Голоса ПРОТИВ: {details['anti_votes']}")
            self.logger.info(f"  Найден полный текст: {len(details['full_text'])} символов")
            self.logger.info(f"  Дата окончания: {details['end_date']}")
            
            return details
            
        except Exception as e:
            self.logger.error(f"Ошибка парсинга деталей {url}: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def get_initiatives_with_details(self, max_initiatives=20):
        """
        Получение инициатив с детальной информацией
        """
        try:
            # Получаем список инициатив
            initiatives = self.parse_federal_initiatives(max_pages=1)
            
            if not initiatives:
                self.logger.warning("Не удалось получить инициативы")
                return []
            
            # Ограничиваем количество
            initiatives = initiatives[:max_initiatives]
            
            # Для каждой инициативы получаем детальную информацию
            for i, initiative in enumerate(initiatives, 1):
                self.logger.info(f"Получение деталей инициативы {i}/{len(initiatives)}: {initiative['title'][:50]}...")
                
                details = self.parse_initiative_details(initiative['url'])
                initiative.update(details)
                
                # Задержка между запросами
                if i < len(initiatives):
                    time.sleep(1)
            
            return initiatives
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении инициатив с деталями: {e}")
            return []

    def save_to_json(self, initiatives, filename=None):
        """Сохранение инициатив в JSON файл"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"exports/federal_initiatives_{timestamp}.json"
        
        try:
            import json
            import os
            
            # Создаем папку, если ее нет
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(initiatives, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Инициативы сохранены в {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения в JSON: {e}")
            return None

def test_parser():
    """Тест парсера"""
    print("=" * 60)
    print("ТЕСТ ПАРСЕРА ROI.RU - ФЕДЕРАЛЬНЫЕ ИНИЦИАТИВЫ")
    print("=" * 60)
    
    parser = ROIParser()
    
    print("\n1. Парсинг федеральных инициатив...")
    initiatives = parser.parse_federal_initiatives(max_pages=1)
    
    if initiatives:
        print(f"\nНайдено инициатив: {len(initiatives)}")
        print("\nПервые 5 инициатив:")
        print("-" * 80)
        
        for i, init in enumerate(initiatives[:5], 1):
            print(f"\n{i}. ID: {init['external_id']}")
            print(f"   Заголовок: {init['title']}")
            print(f"   Голосов: {init['votes']}")
            print(f"   Уровень: {init['level']}")
            print(f"   URL: {init['url']}")
        
        print("\n2. Сохранение в JSON...")
        saved_file = parser.save_to_json(initiatives)
        if saved_file:
            print(f"   ✓ Сохранено в: {saved_file}")
        
        print("\n3. Тест детального парсинга (первая инициатива)...")
        if initiatives:
            details = parser.parse_initiative_details(initiatives[0]['url'])
            if details.get('full_text'):
                print(f"   ✓ Текст инициативы: {details['full_text'][:200]}...")
            if details.get('author'):
                print(f"   ✓ Автор: {details['author']}")
            print(f"   ✓ Статус: {details.get('status', 'неизвестно')}")
        
        print("\n" + "=" * 60)
        print("ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
        print("=" * 60)
        
    else:
        print("\n✗ Не удалось получить инициативы")
        print("Возможные причины:")
        print("1. Проблемы с интернет-соединением")
        print("2. Изменение структуры сайта roi.ru")
        print("3. Сайт требует JavaScript (используйте Selenium)")
    
    return initiatives

if __name__ == "__main__":
    test_parser()