import json
import os
import time
import logging
from collections import defaultdict
from typing import Dict, List, Any, Optional, Set

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class StatsManager:
    """Класс для управления статистикой пользователей"""
    
    def __init__(self, stats_file: str = "stats.json"):
        """
        Инициализация менеджера статистики
        
        Args:
            stats_file: Имя файла для хранения статистики
        """
        self.stats_file = stats_file
        self.stats = self._load_stats()
        self.save_interval = 10  # Интервал автосохранения (количество изменений)
        self.changes_count = 0
        logger.info(f"Менеджер статистики инициализирован с файлом {stats_file}")
    
    def _load_stats(self) -> Dict:
        """
        Загрузка статистики из JSON файла
        
        Returns:
            Словарь со статистикой или пустой словарь в случае ошибки
        """
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    users_count = len(data)
                    logger.info(f"Статистика загружена из {self.stats_file} для {users_count} пользователей")
                    return data
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка чтения файла {self.stats_file}: {e}")
                return {}
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при чтении {self.stats_file}: {e}")
                return {}
        
        logger.info(f"Файл статистики {self.stats_file} не найден, будет создан новый")
        return {}
    
    def _save_stats(self) -> bool:
        """
        Сохранение статистики в JSON файл
        
        Returns:
            True в случае успеха, False в случае ошибки
        """
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as file:
                json.dump(self.stats, file, ensure_ascii=False, indent=4)
            logger.info(f"Статистика сохранена в {self.stats_file}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении статистики в {self.stats_file}: {e}")
            return False
    
    def _auto_save(self) -> None:
        """Автоматическое сохранение статистики через определенное количество изменений"""
        self.changes_count += 1
        if self.changes_count >= self.save_interval:
            self._save_stats()
            self.changes_count = 0
    
    def _get_or_create_user_stats(self, user_id: int) -> Dict:
        """
        Получение или создание статистики для пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Статистика пользователя
        """
        user_id_str = str(user_id)
        
        if user_id_str not in self.stats:
            # Инициализация статистики для нового пользователя
            self.stats[user_id_str] = {
                "tests_total": 0,
                "tests_correct": 0,
                "test_types": {},
                "questions": {}
            }
            logger.info(f"Создана статистика для нового пользователя {user_id}")
        
        return self.stats[user_id_str]
    
    def add_test_result(self, user_id: int, test_type: str, question: str, is_correct: bool) -> None:
        """
        Добавление результата теста в статистику
        
        Args:
            user_id: ID пользователя
            test_type: Тип теста (date, event, figure, achievement)
            question: Текст вопроса
            is_correct: Результат (правильно/неправильно)
        """
        user_stats = self._get_or_create_user_stats(user_id)
        
        # Инициализация статистики по типу теста, если ее еще нет
        if test_type not in user_stats["test_types"]:
            user_stats["test_types"][test_type] = {
                "total": 0,
                "correct": 0
            }
        
        # Инициализация статистики по вопросу, если ее еще нет
        if question not in user_stats["questions"]:
            user_stats["questions"][question] = {
                "test_type": test_type,
                "attempts": 0,
                "correct": 0,
                "last_attempt": 0,
                "history": []
            }
        
        # Обновление общей статистики
        user_stats["tests_total"] += 1
        if is_correct:
            user_stats["tests_correct"] += 1
        
        # Обновление статистики по типу теста
        user_stats["test_types"][test_type]["total"] += 1
        if is_correct:
            user_stats["test_types"][test_type]["correct"] += 1
        
        # Обновление статистики по вопросу
        question_stats = user_stats["questions"][question]
        question_stats["attempts"] += 1
        if is_correct:
            question_stats["correct"] += 1
        
        # Запись времени последней попытки
        current_time = int(time.time())
        question_stats["last_attempt"] = current_time
        
        # Добавление результата в историю
        question_stats["history"].append({
            "timestamp": current_time,
            "is_correct": is_correct
        })
        
        # Ограничение размера истории (для экономии места)
        if len(question_stats["history"]) > 10:
            question_stats["history"] = question_stats["history"][-10:]
        
        # Автоматическое сохранение
        self._auto_save()
        
        logger.debug(f"Добавлен результат теста для пользователя {user_id}: тип={test_type}, правильно={is_correct}")
    
    def get_user_stats(self, user_id: int) -> Dict:
        """
        Получение статистики пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Статистика пользователя
        """
        user_id_str = str(user_id)
        
        # Возвращение пустой статистики, если пользователь не найден
        if user_id_str not in self.stats:
            logger.debug(f"Запрошена статистика для пользователя {user_id}, но он не найден")
            return {
                "tests_total": 0,
                "tests_correct": 0,
                "accuracy": 0,
                "test_types": {}
            }
        
        # Получение статистики
        user_stats = self.stats[user_id_str]
        
        # Расчет точности
        accuracy = 0
        if user_stats["tests_total"] > 0:
            accuracy = round(user_stats["tests_correct"] / user_stats["tests_total"] * 100, 2)
        
        # Формирование результата
        result = {
            "tests_total": user_stats["tests_total"],
            "tests_correct": user_stats["tests_correct"],
            "accuracy": accuracy,
            "test_types": user_stats["test_types"]
        }
        
        logger.debug(f"Возвращена статистика для пользователя {user_id}: всего={result['tests_total']}, точность={result['accuracy']}%")
        return result
    
    def get_difficult_questions(self, user_id: int, limit: int = 5) -> List[Dict]:
        """
        Получение сложных вопросов для пользователя
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество вопросов
            
        Returns:
            Список сложных вопросов
        """
        user_id_str = str(user_id)
        
        # Возвращение пустого списка, если пользователь не найден
        if user_id_str not in self.stats:
            logger.debug(f"Запрошены сложные вопросы для пользователя {user_id}, но он не найден")
            return []
        
        # Получение всех вопросов пользователя
        user_questions = self.stats[user_id_str]["questions"]
        
        # Фильтрация вопросов с несколькими попытками
        difficult_questions = []
        
        for question_text, question_stats in user_questions.items():
            # Пропуск вопросов с менее чем 2 попытками
            if question_stats["attempts"] < 2:
                continue
            
            # Расчет точности
            accuracy = round(question_stats["correct"] / question_stats["attempts"] * 100, 2)
            
            # Добавление вопроса, если точность менее 50%
            if accuracy < 50:
                difficult_questions.append({
                    "question": question_text,
                    "test_type": question_stats["test_type"],
                    "attempts": question_stats["attempts"],
                    "correct": question_stats["correct"],
                    "accuracy": accuracy
                })
        
        # Сортировка по точности (от низкой к высокой)
        difficult_questions.sort(key=lambda q: q["accuracy"])
        
        # Возвращение ограниченного количества вопросов
        logger.debug(f"Найдено {len(difficult_questions)} сложных вопросов для пользователя {user_id}, возвращено {min(limit, len(difficult_questions))}")
        return difficult_questions[:limit]
    
    def get_recently_incorrect_questions(self, user_id: int, limit: int = 5) -> List[Dict]:
        """
        Получение вопросов, на которые пользователь недавно ответил неправильно
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество вопросов
            
        Returns:
            Список недавних неправильных вопросов
        """
        user_id_str = str(user_id)
        
        # Возвращение пустого списка, если пользователь не найден
        if user_id_str not in self.stats:
            logger.debug(f"Запрошены недавние неправильные вопросы для пользователя {user_id}, но он не найден")
            return []
        
        # Получение всех вопросов пользователя
        user_questions = self.stats[user_id_str]["questions"]
        
        # Фильтрация недавних неправильных вопросов
        recent_incorrect = []
        
        for question_text, question_stats in user_questions.items():
            # Проверка последней истории
            if question_stats["history"] and not question_stats["history"][-1]["is_correct"]:
                recent_incorrect.append({
                    "question": question_text,
                    "test_type": question_stats["test_type"],
                    "last_attempt": question_stats["last_attempt"]
                })
        
        # Сортировка по времени последней попытки (от новых к старым)
        recent_incorrect.sort(key=lambda q: q["last_attempt"], reverse=True)
        
        # Возвращение ограниченного количества вопросов
        logger.debug(f"Найдено {len(recent_incorrect)} недавних неправильных вопросов для пользователя {user_id}, возвращено {min(limit, len(recent_incorrect))}")
        return recent_incorrect[:limit]
    
    def get_user_progress(self, user_id: int, days: int = 7) -> Dict:
        """
        Получение прогресса пользователя за последние N дней
        
        Args:
            user_id: ID пользователя
            days: Количество дней для анализа
            
        Returns:
            Данные о прогрессе
        """
        user_id_str = str(user_id)
        
        # Возвращение пустого прогресса, если пользователь не найден
        if user_id_str not in self.stats:
            logger.debug(f"Запрошен прогресс для пользователя {user_id}, но он не найден")
            return {
                "days": [],
                "total_tests": [],
                "accuracy": []
            }
        
        # Получение всех вопросов пользователя
        user_questions = self.stats[user_id_str]["questions"]
        
        # Текущее время
        current_time = int(time.time())
        
        # Расчет начала периода
        period_start = current_time - days * 24 * 60 * 60
        
        # Создание массива дней (от старых к новым)
        day_timestamps = []
        for i in range(days):
            day_start = period_start + i * 24 * 60 * 60
            day_timestamps.append(day_start)
        
        # Инициализация данных прогресса
        progress_data = {
            "days": [time.strftime("%d.%m", time.localtime(ts)) for ts in day_timestamps],
            "total_tests": [0] * days,
            "correct_tests": [0] * days,
            "accuracy": [0] * days
        }
        
        # Обработка истории вопросов
        for question_text, question_stats in user_questions.items():
            for history_item in question_stats["history"]:
                timestamp = history_item["timestamp"]
                
                # Пропуск записей до начала периода
                if timestamp < period_start:
                    continue
                
                # Определение индекса дня
                day_index = min(days - 1, (timestamp - period_start) // (24 * 60 * 60))
                
                # Обновление данных
                progress_data["total_tests"][day_index] += 1
                if history_item["is_correct"]:
                    progress_data["correct_tests"][day_index] += 1
        
        # Расчет точности
        for i in range(days):
            if progress_data["total_tests"][i] > 0:
                progress_data["accuracy"][i] = round(
                    progress_data["correct_tests"][i] / progress_data["total_tests"][i] * 100, 
                    2
                )
            else:
                progress_data["accuracy"][i] = 0
        
        logger.debug(f"Сформирован прогресс за {days} дней для пользователя {user_id}")
        return progress_data
    
    def get_test_type_stats(self, user_id: int) -> Dict:
        """
        Получение детальной статистики по типам тестов
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Словарь со статистикой по типам тестов
        """
        user_id_str = str(user_id)
        
        # Возвращение пустой статистики, если пользователь не найден
        if user_id_str not in self.stats:
            logger.debug(f"Запрошена статистика по типам тестов для пользователя {user_id}, но он не найден")
            return {}
        
        # Получение статистики по типам тестов
        test_types = self.stats[user_id_str]["test_types"]
        
        # Формирование результата с расчетом точности
        result = {}
        for test_type, stats in test_types.items():
            accuracy = 0
            if stats["total"] > 0:
                accuracy = round(stats["correct"] / stats["total"] * 100, 2)
            
            # Определение названия типа теста
            type_name = ""
            if test_type == "date":
                type_name = "Даты"
            elif test_type == "event":
                type_name = "События"
            elif test_type == "figure":
                type_name = "Деятели"
            elif test_type == "achievement":
                type_name = "Достижения"
            else:
                type_name = test_type.capitalize()
            
            result[test_type] = {
                "name": type_name,
                "total": stats["total"],
                "correct": stats["correct"],
                "accuracy": accuracy
            }
        
        logger.debug(f"Возвращена статистика по типам тестов для пользователя {user_id}")
        return result
    
    def get_user_recommendations(self, user_id: int) -> Dict:
        """
        Формирование персональных рекомендаций для пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Словарь с рекомендациями
        """
        user_id_str = str(user_id)
        
        # Возвращение базовых рекомендаций, если пользователь не найден
        if user_id_str not in self.stats:
            logger.debug(f"Запрошены рекомендации для пользователя {user_id}, но он не найден")
            return {
                "general": ["Начните регулярно проходить тесты для отслеживания прогресса"]
            }
        
        # Получение статистики пользователя
        user_stats = self.stats[user_id_str]
        total_tests = user_stats["tests_total"]
        
        # Базовые рекомендации
        if total_tests == 0:
            return {
                "general": ["Начните регулярно проходить тесты для отслеживания прогресса"]
            }
        
        # Инициализация рекомендаций
        recommendations = {
            "general": [],
            "test_types": [],
            "questions": []
        }
        
        # Анализ активности
        if total_tests < 10:
            recommendations["general"].append(
                "Увеличьте количество пройденных тестов для более точной статистики"
            )
        
        # Анализ точности
        accuracy = round(user_stats["tests_correct"] / total_tests * 100, 2)
        if accuracy < 50:
            recommendations["general"].append(
                "Ваша общая точность ниже 50%. Рекомендуем начать с базовых материалов и постепенно переходить к сложным"
            )
        elif accuracy < 70:
            recommendations["general"].append(
                "Используйте режим обучения для регулярного получения и закрепления материала"
            )
        
        # Анализ типов тестов
        test_types = user_stats["test_types"]
        for test_type, stats in test_types.items():
            if stats["total"] >= 5:  # Достаточно данных для анализа
                type_accuracy = round(stats["correct"] / stats["total"] * 100, 2)
                
                # Определение названия типа теста
                type_name = ""
                if test_type == "date":
                    type_name = "даты"
                elif test_type == "event":
                    type_name = "события"
                elif test_type == "figure":
                    type_name = "исторические деятели"
                elif test_type == "achievement":
                    type_name = "достижения"
                else:
                    type_name = test_type
                
                # Рекомендации по типам тестов
                if type_accuracy < 50:
                    recommendations["test_types"].append(
                        f"Уделите больше внимания теме '{type_name}' (точность {type_accuracy}%)"
                    )
        
        # Анализ сложных вопросов
        difficult_questions = self.get_difficult_questions(user_id, limit=3)
        if difficult_questions:
            recommendations["questions"].append(
                "Повторите материал по следующим сложным для вас вопросам:"
            )
            for question in difficult_questions:
                recommendations["questions"].append(
                    f"• {question['question']} (точность {question['accuracy']}%)"
                )
        
        logger.debug(f"Сформированы рекомендации для пользователя {user_id}")
        return recommendations
    
    def reset_user_stats(self, user_id: int) -> bool:
        """
        Сброс статистики пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True в случае успеха, False если пользователь не найден
        """
        user_id_str = str(user_id)
        
        if user_id_str not in self.stats:
            logger.warning(f"Попытка сброса статистики для несуществующего пользователя {user_id}")
            return False
        
        # Сброс статистики
        self.stats[user_id_str] = {
            "tests_total": 0,
            "tests_correct": 0,
            "test_types": {},
            "questions": {}
        }
        
        # Сохранение изменений
        self._save_stats()
        
        logger.info(f"Статистика пользователя {user_id} сброшена")
        return True