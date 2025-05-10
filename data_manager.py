import json
import os
import random
from typing import Dict, List, Tuple, Any, Optional

class DataManager:
    """Класс для управления базой данных исторических событий и деятелей"""
    
    def __init__(self, filename: str):
        """
        Инициализация менеджера данных
        
        Args:
            filename: Имя файла для хранения данных
        """
        self.filename = filename
        self.data = self._load_data()
        
        # Инициализация базы данных, если файл не существует
        if not self.data:
            self.data = {
                "events": [],
                "figures": []
            }
            self._save_data()
    
    def _load_data(self) -> Dict:
        """Загрузка данных из JSON файла"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except json.JSONDecodeError:
                print(f"Ошибка чтения файла {self.filename}. Создание новой базы данных.")
                return {}
        return {}
    
    def _save_data(self) -> None:
        """Сохранение данных в JSON файл"""
        with open(self.filename, 'w', encoding='utf-8') as file:
            json.dump(self.data, file, ensure_ascii=False, indent=4)
    
    def add_event(self, date: str, description: str) -> int:
        """
        Добавление исторического события
        
        Args:
            date: Дата события
            description: Описание события
            
        Returns:
            ID добавленного события
        """
        event_id = len(self.data["events"])
        
        self.data["events"].append({
            "id": event_id,
            "date": date,
            "description": description
        })
        
        self._save_data()
        return event_id
    
    def add_figure(self, name: str, achievement: str) -> int:
        """
        Добавление исторического деятеля
        
        Args:
            name: Имя деятеля
            achievement: Достижения деятеля
            
        Returns:
            ID добавленного деятеля
        """
        figure_id = len(self.data["figures"])
        
        self.data["figures"].append({
            "id": figure_id,
            "name": name,
            "achievement": achievement
        })
        
        self._save_data()
        return figure_id
    
    def get_random_events(self, count: int) -> List[Dict]:
        """
        Получение случайных исторических событий
        
        Args:
            count: Количество событий
            
        Returns:
            Список случайных событий
        """
        events = self.data["events"].copy()
        
        if not events:
            return []
        
        random.shuffle(events)
        return events[:min(count, len(events))]
    
    def get_random_figures(self, count: int) -> List[Dict]:
        """
        Получение случайных исторических деятелей
        
        Args:
            count: Количество деятелей
            
        Returns:
            Список случайных деятелей
        """
        figures = self.data["figures"].copy()
        
        if not figures:
            return []
        
        random.shuffle(figures)
        return figures[:min(count, len(figures))]
    
    def get_event_by_date(self, date: str) -> Optional[Dict]:
        """
        Получение события по дате
        
        Args:
            date: Дата события
            
        Returns:
            Событие или None, если событие не найдено
        """
        for event in self.data["events"]:
            if event["date"] == date:
                return event
        return None
    
    def get_event_by_description(self, description: str) -> Optional[Dict]:
        """
        Получение события по описанию
        
        Args:
            description: Описание события
            
        Returns:
            Событие или None, если событие не найдено
        """
        for event in self.data["events"]:
            if event["description"].lower() == description.lower():
                return event
        return None
    
    def get_figure_by_name(self, name: str) -> Optional[Dict]:
        """
        Получение деятеля по имени
        
        Args:
            name: Имя деятеля
            
        Returns:
            Деятель или None, если деятель не найден
        """
        for figure in self.data["figures"]:
            if figure["name"].lower() == name.lower():
                return figure
        return None
    
    def get_figure_by_achievement(self, achievement: str) -> Optional[Dict]:
        """
        Получение деятеля по достижению
        
        Args:
            achievement: Достижение деятеля
            
        Returns:
            Деятель или None, если деятель не найден
        """
        for figure in self.data["figures"]:
            if figure["achievement"].lower() == achievement.lower():
                return figure
        return None
    
    def get_random_event(self) -> Optional[Dict]:
        """
        Получение случайного события
        
        Returns:
            Случайное событие или None, если база пуста
        """
        events = self.data["events"]
        if not events:
            return None
        return random.choice(events)
    
    def get_random_figure(self) -> Optional[Dict]:
        """
        Получение случайного деятеля
        
        Returns:
            Случайный деятель или None, если база пуста
        """
        figures = self.data["figures"]
        if not figures:
            return None
        return random.choice(figures)
    
    def get_all_events(self) -> List[Dict]:
        """
        Получение всех событий
        
        Returns:
            Список всех событий
        """
        return self.data["events"]
    
    def get_all_figures(self) -> List[Dict]:
        """
        Получение всех деятелей
        
        Returns:
            Список всех деятелей
        """
        return self.data["figures"]
    
    def initialize_sample_data(self) -> None:
        """Инициализация примерными данными"""
        # Проверяем, пуста ли база данных
        if self.data["events"] or self.data["figures"]:
            return  # База данных уже содержит данные
        
        # Примерные события
        sample_events = [
            {"date": "1569", "description": "Люблинская уния. Объединение Великого княжества Литовского и Королевства Польского в Речь Посполитую"},
            {"date": "1791", "description": "Принятие Конституции Речи Посполитой 3 мая"},
            {"date": "1794", "description": "Восстание под руководством Тадеуша Костюшко"},
            {"date": "1795", "description": "Третий раздел Речи Посполитой. Включение белорусских земель в состав Российской империи"},
            {"date": "1812", "description": "Отечественная война 1812 года. Сражения на территории Беларуси"},
            {"date": "1863-1864", "description": "Восстание под руководством К. Калиновского"},
            {"date": "1917", "description": "Февральская и Октябрьская революции"},
            {"date": "1918", "description": "Провозглашение Белорусской Народной Республики (БНР)"},
            {"date": "1919", "description": "Создание Белорусской ССР (БССР)"},
            {"date": "1941-1944", "description": "Великая Отечественная война на территории Беларуси"},
            {"date": "1986", "description": "Авария на Чернобыльской АЭС"},
            {"date": "1991", "description": "Провозглашение независимости Республики Беларусь"},
            {"date": "1994", "description": "Принятие Конституции Республики Беларусь, первые президентские выборы"}
        ]
        
        # Примерные исторические деятели
        sample_figures = [
            {"name": "Франциск Скорина", "achievement": "Белорусский первопечатник, просветитель, переводчик Библии на старобелорусский язык"},
            {"name": "Кастусь Калиновский", "achievement": "Лидер национально-освободительного восстания 1863-1864 годов, публицист"},
            {"name": "Евфросиния Полоцкая", "achievement": "Просветительница, основательница монастырей и школ в Полоцке"},
            {"name": "Петр Мстиславец", "achievement": "Белорусский первопечатник, соратник Ивана Федорова"},
            {"name": "Тадеуш Костюшко", "achievement": "Руководитель восстания 1794 года, национальный герой Беларуси, Польши и США"},
            {"name": "Якуб Колас", "achievement": "Народный поэт Беларуси, один из основателей новой белорусской литературы"},
            {"name": "Янка Купала", "achievement": "Народный поэт Беларуси, классик белорусской литературы, драматург"},
            {"name": "Максим Богданович", "achievement": "Белорусский поэт, прозаик, публицист, литературовед, переводчик"}
        ]
        
        # Добавление примерных данных
        for event in sample_events:
            self.add_event(event["date"], event["description"])
        
        for figure in sample_figures:
            self.add_figure(figure["name"], figure["achievement"])
