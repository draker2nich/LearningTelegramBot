import random
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple, Any

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from data_manager import DataManager
from stats_manager import StatsManager

class KnowledgeTest:
    """Класс для проверки знаний пользователя"""
    
    def __init__(self, data_manager: DataManager):
        """
        Инициализация тестера знаний
        
        Args:
            data_manager: Менеджер данных для получения событий и деятелей
        """
        self.data_manager = data_manager
        # Отслеживание уже использованных вопросов в текущей сессии
        self.used_events = {}  # user_id -> [event_ids]
        self.used_figures = {}  # user_id -> [figure_ids]
    
    async def start_date_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Начало теста по дате
        
        Args:
            update: Объект обновления Telegram
            context: Контекст Telegram-бота
        """
        query = update.callback_query
        user_id = update.effective_user.id
        
        # Инициализация отслеживания использованных событий для пользователя
        if user_id not in self.used_events:
            self.used_events[user_id] = []
        
        # Получение всех событий
        all_events = self.data_manager.get_all_events()
        
        # Фильтрация событий, которые ещё не были использованы
        available_events = [event for event in all_events if event["id"] not in self.used_events[user_id]]
        
        # Если все события уже использованы, сбрасываем список использованных
        if not available_events:
            self.used_events[user_id] = []
            available_events = all_events
        
        # Получение случайного события из доступных
        event = random.choice(available_events)
        
        # Отмечаем событие как использованное
        self.used_events[user_id].append(event["id"])
        
        if not event:
            error_message = (
                "К сожалению, в базе данных нет событий. "
                "Пожалуйста, добавьте события перед началом тестирования."
            )
            if query:
                await query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)
            context.user_data["state"] = None
            return
        
        # Сохранение текущего события для последующей проверки
        context.user_data["current_test"] = {
            "type": "date",
            "event": event
        }
        
        # Отправка вопроса пользователю
        question_message = (
            f"📅 *{event['date']}*\n\n"
            f"Какое историческое событие произошло в эту дату? Опишите своими словами."
        )
        
        if query:
            await query.edit_message_text(
                question_message,
                parse_mode="Markdown"
            )
        else:
            # Это может быть вызов из другой функции
            chat_id = update.effective_chat.id
            await context.bot.send_message(
                chat_id=chat_id,
                text=question_message,
                parse_mode="Markdown"
            )
    
    async def start_event_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Начало теста по событию
        
        Args:
            update: Объект обновления Telegram
            context: Контекст Telegram-бота
        """
        query = update.callback_query
        user_id = update.effective_user.id
        
        # Инициализация отслеживания использованных событий для пользователя
        if user_id not in self.used_events:
            self.used_events[user_id] = []
        
        # Получение всех событий
        all_events = self.data_manager.get_all_events()
        
        # Фильтрация событий, которые ещё не были использованы
        available_events = [event for event in all_events if event["id"] not in self.used_events[user_id]]
        
        # Если все события уже использованы, сбрасываем список использованных
        if not available_events:
            self.used_events[user_id] = []
            available_events = all_events
        
        # Получение случайного события из доступных
        event = random.choice(available_events)
        
        # Отмечаем событие как использованное
        self.used_events[user_id].append(event["id"])
        
        if not event:
            error_message = (
                "К сожалению, в базе данных нет событий. "
                "Пожалуйста, добавьте события перед началом тестирования."
            )
            if query:
                await query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)
            context.user_data["state"] = None
            return
        
        # Сохранение текущего события для последующей проверки
        context.user_data["current_test"] = {
            "type": "event",
            "event": event
        }
        
        # Отправка вопроса пользователю
        question_message = (
            f"🔍 *Событие:* {event['description']}\n\n"
            f"Когда произошло это событие? Укажите дату."
        )
        
        if query:
            await query.edit_message_text(
                question_message,
                parse_mode="Markdown"
            )
        else:
            # Это может быть вызов из другой функции
            chat_id = update.effective_chat.id
            await context.bot.send_message(
                chat_id=chat_id,
                text=question_message,
                parse_mode="Markdown"
            )
    
    async def start_figure_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Начало теста по историческому деятелю
        
        Args:
            update: Объект обновления Telegram
            context: Контекст Telegram-бота
        """
        query = update.callback_query
        user_id = update.effective_user.id
        
        # Инициализация отслеживания использованных деятелей для пользователя
        if user_id not in self.used_figures:
            self.used_figures[user_id] = []
        
        # Получение всех деятелей
        all_figures = self.data_manager.get_all_figures()
        
        # Фильтрация деятелей, которые ещё не были использованы
        available_figures = [figure for figure in all_figures if figure["id"] not in self.used_figures[user_id]]
        
        # Если все деятели уже использованы, сбрасываем список использованных
        if not available_figures:
            self.used_figures[user_id] = []
            available_figures = all_figures
        
        # Получение случайного деятеля из доступных
        figure = random.choice(available_figures)
        
        # Отмечаем деятеля как использованного
        self.used_figures[user_id].append(figure["id"])
        
        if not figure:
            error_message = (
                "К сожалению, в базе данных нет исторических деятелей. "
                "Пожалуйста, добавьте деятелей перед началом тестирования."
            )
            if query:
                await query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)
            context.user_data["state"] = None
            return
        
        # Сохранение текущего деятеля для последующей проверки
        context.user_data["current_test"] = {
            "type": "figure",
            "figure": figure
        }
        
        # Отправка вопроса пользователю
        question_message = (
            f"👤 *{figure['name']}*\n\n"
            f"Чем прославился этот исторический деятель? Опишите его основные достижения."
        )
        
        if query:
            await query.edit_message_text(
                question_message,
                parse_mode="Markdown"
            )
        else:
            # Это может быть вызов из другой функции
            chat_id = update.effective_chat.id
            await context.bot.send_message(
                chat_id=chat_id,
                text=question_message,
                parse_mode="Markdown"
            )
    
    async def start_achievement_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Начало теста по достижению
        
        Args:
            update: Объект обновления Telegram
            context: Контекст Telegram-бота
        """
        query = update.callback_query
        user_id = update.effective_user.id
        
        # Инициализация отслеживания использованных деятелей для пользователя
        if user_id not in self.used_figures:
            self.used_figures[user_id] = []
        
        # Получение всех деятелей
        all_figures = self.data_manager.get_all_figures()
        
        # Фильтрация деятелей, которые ещё не были использованы
        available_figures = [figure for figure in all_figures if figure["id"] not in self.used_figures[user_id]]
        
        # Если все деятели уже использованы, сбрасываем список использованных
        if not available_figures:
            self.used_figures[user_id] = []
            available_figures = all_figures
        
        # Получение случайного деятеля из доступных
        figure = random.choice(available_figures)
        
        # Отмечаем деятеля как использованного
        self.used_figures[user_id].append(figure["id"])
        
        if not figure:
            error_message = (
                "К сожалению, в базе данных нет исторических деятелей. "
                "Пожалуйста, добавьте деятелей перед началом тестирования."
            )
            if query:
                await query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)
            context.user_data["state"] = None
            return
        
        # Сохранение текущего деятеля для последующей проверки
        context.user_data["current_test"] = {
            "type": "achievement",
            "figure": figure
        }
        
        # Отправка вопроса пользователю
        question_message = (
            f"🏆 *Достижение:* {figure['achievement']}\n\n"
            f"Какой исторический деятель известен этим? Укажите полное имя."
        )
        
        if query:
            await query.edit_message_text(
                question_message,
                parse_mode="Markdown"
            )
        else:
            # Это может быть вызов из другой функции
            chat_id = update.effective_chat.id
            await context.bot.send_message(
                chat_id=chat_id,
                text=question_message,
                parse_mode="Markdown"
            )
    
    async def check_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE, stats_manager: StatsManager) -> bool:
        """
        Проверка ответа пользователя
        
        Args:
            update: Объект обновления Telegram
            context: Контекст Telegram-бота
            stats_manager: Менеджер статистики
            
        Returns:
            True, если ответ правильный, False в противном случае
        """
        # Получение текущего теста
        current_test = context.user_data.get("current_test")
        
        if not current_test:
            await update.message.reply_text(
                "⚠️ Произошла ошибка. Пожалуйста, начните тестирование заново."
            )
            return False
        
        user_answer = update.message.text
        user_id = update.effective_user.id
        
        # Проверка ответа в зависимости от типа теста
        if current_test["type"] == "date":
            event = current_test["event"]
            correct_answer = event["description"]
            
            # Улучшенная проверка ответа на вопрос по дате
            similarity = self._calculate_similarity(user_answer, correct_answer)
            
            # Дополнительная проверка на ключевые слова
            keywords = self._extract_keywords(correct_answer)
            keyword_match = self._check_keywords(user_answer, keywords)
            
            # Комбинированная оценка с учетом ключевых слов и общей схожести
            is_correct = similarity >= 0.6 or keyword_match >= 0.7
            
            # Формирование результата с советами
            result_message = self._format_date_result(is_correct, event)
            
            # Обновление статистики
            stats_manager.add_test_result(
                user_id=user_id,
                test_type="date",
                question=f"Дата: {event['date']}",
                is_correct=is_correct
            )
        
        elif current_test["type"] == "event":
            event = current_test["event"]
            correct_answer = event["date"]
            
            # Улучшенная проверка для дат и периодов
            is_correct = self._check_date_answer(user_answer, correct_answer)
            
            # Формирование результата с советами
            result_message = self._format_event_result(is_correct, event)
            
            # Обновление статистики
            stats_manager.add_test_result(
                user_id=user_id,
                test_type="event",
                question=f"Событие: {event['description']}",
                is_correct=is_correct
            )
        
        elif current_test["type"] == "figure":
            figure = current_test["figure"]
            correct_answer = figure["achievement"]
            
            # Улучшенная проверка ответа на вопрос о деятеле
            similarity = self._calculate_similarity(user_answer, correct_answer)
            
            # Дополнительная проверка на ключевые слова
            keywords = self._extract_keywords(correct_answer)
            keyword_match = self._check_keywords(user_answer, keywords)
            
            # Комбинированная оценка
            is_correct = similarity >= 0.6 or keyword_match >= 0.7
            
            # Формирование результата с советами
            result_message = self._format_figure_result(is_correct, figure)
            
            # Обновление статистики
            stats_manager.add_test_result(
                user_id=user_id,
                test_type="figure",
                question=f"Деятель: {figure['name']}",
                is_correct=is_correct
            )
        
        elif current_test["type"] == "achievement":
            figure = current_test["figure"]
            correct_answer = figure["name"]
            
            # Улучшенная проверка имени
            name_similarity = self._calculate_name_similarity(user_answer, correct_answer)
            is_correct = name_similarity >= 0.8
            
            # Формирование результата с советами
            result_message = self._format_achievement_result(is_correct, figure)
            
            # Обновление статистики
            stats_manager.add_test_result(
                user_id=user_id,
                test_type="achievement",
                question=f"Достижение: {figure['achievement']}",
                is_correct=is_correct
            )
        
        else:
            await update.message.reply_text(
                "⚠️ Произошла ошибка. Неизвестный тип теста."
            )
            return False
        
        # Отправка результата пользователю
        await update.message.reply_text(
            result_message,
            parse_mode="Markdown"
        )
        
        return is_correct
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Извлечение ключевых слов из текста
        
        Args:
            text: Исходный текст
            
        Returns:
            Список ключевых слов
        """
        # Удаление знаков препинания и приведение к нижнему регистру
        text = text.lower()
        for char in ".,;:!?—()-\"\'":
            text = text.replace(char, " ")
        
        # Разбиение на слова
        words = text.split()
        
        # Фильтрация стоп-слов (можно расширить список)
        stop_words = ["в", "на", "и", "с", "по", "а", "о", "у", "к", "от", "до", "из", "для", "за", "под", "над"]
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        return keywords
    
    def _check_keywords(self, answer: str, keywords: List[str]) -> float:
        """
        Проверка наличия ключевых слов в ответе
        
        Args:
            answer: Ответ пользователя
            keywords: Список ключевых слов
            
        Returns:
            Доля найденных ключевых слов (от 0 до 1)
        """
        if not keywords:
            return 0
        
        # Приведение ответа к нижнему регистру
        answer = answer.lower()
        
        # Подсчет найденных ключевых слов
        found = 0
        for keyword in keywords:
            if keyword in answer:
                found += 1
        
        # Возвращение доли найденных ключевых слов
        return found / len(keywords)
    
    def _check_date_answer(self, user_answer: str, correct_answer: str) -> bool:
        """
        Улучшенная проверка ответа на вопрос о дате
        
        Args:
            user_answer: Ответ пользователя
            correct_answer: Правильный ответ
            
        Returns:
            True, если ответ правильный, False в противном случае
        """
        # Предварительная обработка ответов
        user_answer = user_answer.strip().lower()
        correct_answer = correct_answer.strip().lower()
        
        # Прямое сравнение
        if user_answer == correct_answer:
            return True
        
        # Проверка сложных форматов дат
        if "-" in correct_answer:
            # Период (например, 1941-1944)
            try:
                correct_start, correct_end = map(int, correct_answer.split("-"))
                
                # Проверка, указал ли пользователь только одну дату из периода
                if user_answer.isdigit():
                    user_date = int(user_answer)
                    return correct_start <= user_date <= correct_end
                
                # Проверка, указал ли пользователь период
                if "-" in user_answer:
                    user_start, user_end = map(int, user_answer.split("-"))
                    return (user_start == correct_start and user_end == correct_end)
            except (ValueError, TypeError):
                pass
        
        # Обработка дат, содержащих месяц
        if " " in correct_answer:
            # Проверка, содержит ли ответ пользователя год из правильного ответа
            correct_parts = correct_answer.split()
            if any(part.isdigit() and part in user_answer for part in correct_parts):
                return True
        
        # Проверка на близость (для простых годов)
        if correct_answer.isdigit() and user_answer.isdigit():
            return correct_answer == user_answer
        
        # Проверка на схожесть текста
        return self._calculate_similarity(user_answer, correct_answer) >= 0.8
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Расчет схожести двух строк
        
        Args:
            str1: Первая строка
            str2: Вторая строка
            
        Returns:
            Значение схожести от 0 до 1
        """
        # Приведение к нижнему регистру для регистронезависимого сравнения
        str1 = str1.lower()
        str2 = str2.lower()
        
        # Использование алгоритма SequenceMatcher для нечеткого сравнения
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _calculate_name_similarity(self, user_name: str, correct_name: str) -> float:
        """
        Специализированная функция для сравнения имен
        
        Args:
            user_name: Имя, введенное пользователем
            correct_name: Правильное имя
            
        Returns:
            Значение схожести от 0 до 1
        """
        # Приведение к нижнему регистру
        user_name = user_name.lower()
        correct_name = correct_name.lower()
        
        # Прямое сравнение
        if user_name == correct_name:
            return 1.0
        
        # Разбиение имени на части (имя и фамилия)
        user_parts = [part.strip() for part in user_name.split()]
        correct_parts = [part.strip() for part in correct_name.split()]
        
        # Проверка частей имени
        matched_parts = 0
        total_parts = len(correct_parts)
        
        for correct_part in correct_parts:
            for user_part in user_parts:
                if self._calculate_similarity(user_part, correct_part) > 0.8:
                    matched_parts += 1
                    break
        
        # Возвращение доли совпавших частей
        return matched_parts / total_parts if total_parts > 0 else 0.0
    
    def _format_date_result(self, is_correct: bool, event: Dict) -> str:
        """
        Форматирование результата теста по дате
        
        Args:
            is_correct: Правильность ответа
            event: Информация о событии
            
        Returns:
            Отформатированное сообщение
        """
        result = "✅ Правильно!" if is_correct else "❌ Неправильно."
        result += f"\n\n📅 *{event['date']}*: {event['description']}"
        
        # Добавление совета
        if not is_correct:
            result += "\n\n💡 *Совет:* Для запоминания дат связывайте их с контекстом эпохи или другими событиями, "
            result += "составляйте хронологические таблицы и регулярно повторяйте."
        
        return result
    
    def _format_event_result(self, is_correct: bool, event: Dict) -> str:
        """
        Форматирование результата теста по событию
        
        Args:
            is_correct: Правильность ответа
            event: Информация о событии
            
        Returns:
            Отформатированное сообщение
        """
        result = "✅ Правильно!" if is_correct else "❌ Неправильно."
        result += f"\n\n🔍 *Событие:* {event['description']}\n📅 *Дата:* {event['date']}"
        
        # Добавление совета
        if not is_correct:
            result += "\n\n💡 *Совет:* Группируйте события по историческим периодам и изучайте их в контексте "
            result += "причин и последствий для лучшего запоминания дат."
        
        return result
    
    def _format_figure_result(self, is_correct: bool, figure: Dict) -> str:
        """
        Форматирование результата теста по историческому деятелю
        
        Args:
            is_correct: Правильность ответа
            figure: Информация о деятеле
            
        Returns:
            Отформатированное сообщение
        """
        result = "✅ Правильно!" if is_correct else "❌ Неправильно."
        result += f"\n\n👤 *{figure['name']}*: {figure['achievement']}"
        
        # Добавление совета
        if not is_correct:
            result += "\n\n💡 *Совет:* Создавайте мнемонические ассоциации между историческими деятелями "
            result += "и их достижениями, группируйте их по сферам деятельности или эпохам."
        
        return result
    
    def _format_achievement_result(self, is_correct: bool, figure: Dict) -> str:
        """
        Форматирование результата теста по достижению
        
        Args:
            is_correct: Правильность ответа
            figure: Информация о деятеле
            
        Returns:
            Отформатированное сообщение
        """
        result = "✅ Правильно!" if is_correct else "❌ Неправильно."
        result += f"\n\n🏆 *Достижение:* {figure['achievement']}\n👤 *Деятель:* {figure['name']}"
        
        # Добавление совета
        if not is_correct:
            result += "\n\n💡 *Совет:* Создайте карточки, где на одной стороне достижение, а на другой — имя деятеля. "
            result += "Тренируйтесь, вспоминая имя по достижению и наоборот."
        
        return result
    
    async def start_marathon(self, update: Update, context: ContextTypes.DEFAULT_TYPE, questions_count: int = 5) -> None:
        """
        Начало марафона (серии тестов разных типов)
        
        Args:
            update: Объект обновления Telegram
            context: Контекст Telegram-бота
            questions_count: Количество вопросов в марафоне
        """
        # Инициализация марафона
        context.user_data["marathon"] = {
            "questions_count": questions_count,
            "current_question": 0,
            "correct_answers": 0,
            "questions": [],
            "history": []  # Для хранения истории вопросов и ответов
        }
        
        # Генерация последовательности типов вопросов с равномерным распределением
        question_types = ["date", "event", "figure", "achievement"]
        questions = []
        
        # Обеспечиваем, чтобы все типы вопросов были представлены
        base_questions = question_types.copy()
        random.shuffle(base_questions)
        questions.extend(base_questions)
        
        # Добавляем дополнительные случайные вопросы, если нужно
        while len(questions) < questions_count:
            questions.append(random.choice(question_types))
        
        # Обрезаем список, если он превышает требуемое количество
        questions = questions[:questions_count]
        random.shuffle(questions)
        
        context.user_data["marathon"]["questions"] = questions
        
        # Запуск первого вопроса
        await self.next_marathon_question(update, context)
    
    async def next_marathon_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Переход к следующему вопросу марафона
        
        Args:
            update: Объект обновления Telegram
            context: Контекст Telegram-бота
        """
        marathon = context.user_data.get("marathon")
        
        if not marathon:
            # Если марафон не инициализирован, сообщить об ошибке
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    "⚠️ Марафон не инициализирован. Пожалуйста, начните заново."
                )
            else:
                await update.message.reply_text(
                    "⚠️ Марафон не инициализирован. Пожалуйста, начните заново."
                )
            return
        
        # Проверка, не закончился ли марафон
        current_question = marathon["current_question"]
        if current_question >= marathon["questions_count"]:
            # Марафон завершен
            await self.finish_marathon(update, context)
            return
        
        # Определение типа текущего вопроса
        question_type = marathon["questions"][current_question]
        context.user_data["state"] = "marathon"
        
        # Отображение номера вопроса и прогресса
        progress_message = (
            f"🏆 *Марафон: вопрос {current_question + 1} из {marathon['questions_count']}*\n\n"
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                progress_message,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                progress_message,
                parse_mode="Markdown"
            )
        
        # Запуск соответствующего теста
        if question_type == "date":
            await self.start_date_test(update, context)
        elif question_type == "event":
            await self.start_event_test(update, context)
        elif question_type == "figure":
            await self.start_figure_test(update, context)
        elif question_type == "achievement":
            await self.start_achievement_test(update, context)
        
        # Увеличение счетчика вопросов
        marathon["current_question"] += 1
    
    async def check_marathon_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE, stats_manager: StatsManager) -> None:
        """
        Проверка ответа в режиме марафона
        
        Args:
            update: Объект обновления Telegram
            context: Контекст Telegram-бота
            stats_manager: Менеджер статистики
        """
        # Проверка ответа обычным способом
        is_correct = await self.check_answer(update, context, stats_manager)
        
        # Получение текущего теста
        current_test = context.user_data.get("current_test")
        
        # Сохранение информации о вопросе и ответе
        if current_test:
            question_info = {
                "type": current_test["type"],
                "is_correct": is_correct
            }
            
            if current_test["type"] in ["date", "event"]:
                question_info["content"] = current_test["event"]
            else:
                question_info["content"] = current_test["figure"]
            
            # Добавление информации в историю марафона
            context.user_data["marathon"]["history"].append(question_info)
        
        # Обновление счетчика правильных ответов
        if is_correct:
            context.user_data["marathon"]["correct_answers"] += 1
        
        # Предложение перейти к следующему вопросу
        keyboard = [
            [InlineKeyboardButton("Следующий вопрос", callback_data="next_marathon_question")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Нажмите кнопку, чтобы перейти к следующему вопросу марафона.",
            reply_markup=reply_markup
        )
    
    async def finish_marathon(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Завершение марафона и отображение результатов
        
        Args:
            update: Объект обновления Telegram
            context: Контекст Telegram-бота
        """
        marathon = context.user_data["marathon"]
        correct_answers = marathon["correct_answers"]
        total_questions = marathon["questions_count"]
        accuracy = round(correct_answers / total_questions * 100, 2)
        
        # Формирование сообщения с результатами
        result_message = (
            f"🏁 *Марафон завершен!*\n\n"
            f"Ваш результат: *{correct_answers} из {total_questions}* ({accuracy}%)\n\n"
        )
        
        # Добавление истории вопросов и ответов
        if marathon.get("history"):
            result_message += "*История марафона:*\n"
            
            for i, question in enumerate(marathon["history"], 1):
                # Определение типа вопроса
                type_name = ""
                if question["type"] == "date":
                    type_name = "Дата"
                    question_text = question["content"]["date"]
                    answer_text = question["content"]["description"]
                elif question["type"] == "event":
                    type_name = "Событие"
                    question_text = question["content"]["description"]
                    answer_text = question["content"]["date"]
                elif question["type"] == "figure":
                    type_name = "Деятель"
                    question_text = question["content"]["name"]
                    answer_text = question["content"]["achievement"]
                elif question["type"] == "achievement":
                    type_name = "Достижение"
                    question_text = question["content"]["achievement"]
                    answer_text = question["content"]["name"]
                
                # Добавление информации о вопросе
                result_message += f"{i}. {type_name}: "
                result_message += f"{question_text[:30]}{'...' if len(question_text) > 30 else ''} "
                result_message += "✅" if question["is_correct"] else "❌"
                result_message += "\n"
        
        # Добавление рекомендаций
        if accuracy < 50:
            result_message += "\n💡 *Рекомендации:* Вам стоит больше внимания уделить систематическому изучению материала. "
            result_message += "Используйте режим обучения для регулярного получения информации."
        elif accuracy < 70:
            result_message += "\n💡 *Рекомендации:* Неплохой результат, но есть над чем работать. "
            result_message += "Сосредоточьтесь на тех типах вопросов, где у вас больше ошибок."
        else:
            result_message += "\n💡 *Рекомендации:* Отличный результат! Продолжайте регулярные тренировки "
            result_message += "для поддержания и улучшения ваших знаний."
        
        # Кнопки для дальнейших действий
        keyboard = [
            [InlineKeyboardButton("Новый марафон", callback_data="start_marathon")],
            [InlineKeyboardButton("Показать статистику", callback_data="statistics")],
            [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                result_message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=result_message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        # Очистка данных марафона
        context.user_data["marathon"] = None
        context.user_data["state"] = None