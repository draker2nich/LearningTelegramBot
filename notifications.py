import datetime
import json
import os
import random
import logging
from typing import Dict, List, Any, Optional, Set, Tuple

from telegram import Update
from telegram.ext import ContextTypes

from data_manager import DataManager

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class NotificationManager:
    """Класс для управления уведомлениями"""
    
    def __init__(self, data_manager: DataManager, notifications_file: str = "notifications.json"):
        """
        Инициализация менеджера уведомлений
        
        Args:
            data_manager: Менеджер данных для получения событий и деятелей
            notifications_file: Имя файла для хранения настроек уведомлений
        """
        self.data_manager = data_manager
        self.notifications_file = notifications_file
        self.user_notifications = self._load_notifications()
        
        # Отслеживание отправленных данных для каждого пользователя
        self.sent_events = {}     # user_id -> set(event_ids)
        self.sent_figures = {}    # user_id -> set(figure_ids)
        
        # Кэш для часовых поясов пользователей
        self.user_timezones = {}  # user_id -> timezone_offset
        
        # Отслеживание последней отправки
        self.last_send_time = {}  # user_id -> Dict[notification_time, last_send_timestamp]
        
        logger.info(f"Инициализирован NotificationManager с {len(self.user_notifications)} пользователями")
    
    def _load_notifications(self) -> Dict:
        """
        Загрузка настроек уведомлений из JSON файла
        
        Returns:
            Словарь с настройками уведомлений
        """
        if os.path.exists(self.notifications_file):
            try:
                with open(self.notifications_file, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    logger.info(f"Загружены настройки уведомлений: {len(data)} пользователей")
                    
                    # Валидация и нормализация данных
                    normalized_data = {}
                    for user_id, notifications in data.items():
                        valid_notifications = []
                        for notification in notifications:
                            # Проверка обязательных полей
                            if all(field in notification for field in ["time", "events_count", "figures_count"]):
                                # Нормализация формата времени
                                notification["time"] = self._normalize_time_format(notification["time"])
                                valid_notifications.append(notification)
                            else:
                                logger.warning(f"Пропущено некорректное уведомление для пользователя {user_id}: {notification}")
                        
                        if valid_notifications:
                            normalized_data[user_id] = valid_notifications
                    
                    return normalized_data
            except json.JSONDecodeError:
                logger.error(f"Ошибка чтения файла {self.notifications_file}. Создание нового файла.")
                return {}
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при чтении {self.notifications_file}: {e}")
                return {}
        return {}
    
    def _normalize_time_format(self, time_str: str) -> str:
        """
        Нормализация формата времени
        
        Args:
            time_str: Строка с временем
            
        Returns:
            Нормализованная строка с временем в формате HH:MM
        """
        try:
            # Разбиение строки на часы и минуты
            parts = time_str.strip().split(":")
            if len(parts) != 2:
                return time_str
            
            # Преобразование в числа
            hour = int(parts[0])
            minute = int(parts[1])
            
            # Проверка допустимых значений
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                # Форматирование с ведущими нулями
                return f"{hour:02d}:{minute:02d}"
            else:
                return time_str
        except (ValueError, IndexError):
            # Если формат некорректный, возвращаем исходную строку
            return time_str
    
    def _save_notifications(self) -> bool:
        """
        Сохранение настроек уведомлений в JSON файл
        
        Returns:
            True в случае успеха, False в случае ошибки
        """
        try:
            with open(self.notifications_file, 'w', encoding='utf-8') as file:
                json.dump(self.user_notifications, file, ensure_ascii=False, indent=4)
            logger.info(f"Сохранены настройки уведомлений для {len(self.user_notifications)} пользователей")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении настроек уведомлений: {e}")
            return False
    
    def add_user_notification(self, user_id: int, notification: Dict) -> bool:
        """
        Добавление настройки уведомления для пользователя
        
        Args:
            user_id: ID пользователя
            notification: Настройка уведомления (время, количество событий, количество деятелей)
            
        Returns:
            True в случае успеха, False в случае ошибки
        """
        # Валидация данных
        if not self._validate_notification(notification):
            logger.error(f"Некорректные данные уведомления: {notification}")
            return False
        
        # Стандартизация формата времени
        notification["time"] = self._normalize_time_format(notification["time"])
        
        user_id_str = str(user_id)
        
        if user_id_str not in self.user_notifications:
            self.user_notifications[user_id_str] = []
        
        # Удаление старой настройки с тем же временем, если она существует
        self.user_notifications[user_id_str] = [
            n for n in self.user_notifications[user_id_str]
            if n["time"] != notification["time"]
        ]
        
        # Добавление новой настройки
        self.user_notifications[user_id_str].append(notification)
        
        # Сохранение изменений
        success = self._save_notifications()
        
        if success:
            logger.info(f"Добавлено уведомление для пользователя {user_id} на время {notification['time']}")
        
        return success
    
    def _validate_notification(self, notification: Dict) -> bool:
        """
        Проверка корректности настройки уведомления
        
        Args:
            notification: Настройка уведомления
            
        Returns:
            True, если настройка корректна, False в противном случае
        """
        # Проверка наличия обязательных полей
        if not all(field in notification for field in ["time", "events_count", "figures_count"]):
            return False
        
        # Проверка формата времени
        time_str = notification["time"]
        try:
            # Разбиение строки на часы и минуты
            parts = time_str.strip().split(":")
            if len(parts) != 2:
                return False
            
            # Преобразование в числа
            hour = int(parts[0])
            minute = int(parts[1])
            
            # Проверка допустимых значений
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                return False
        except (ValueError, IndexError):
            return False
        
        # Проверка типов и диапазонов значений
        try:
            events_count = int(notification["events_count"])
            figures_count = int(notification["figures_count"])
            
            if events_count < 0 or figures_count < 0:
                return False
            
            # Общее количество материалов не должно быть слишком большим
            if events_count + figures_count > 20:
                return False
        except (ValueError, TypeError):
            return False
        
        return True
    
    def replace_all_user_notifications(self, user_id: int, notifications: List[Dict]) -> bool:
        """
        Полная замена всех уведомлений пользователя новым списком
        
        Args:
            user_id: ID пользователя
            notifications: Список новых настроек уведомлений
            
        Returns:
            True в случае успеха, False в случае ошибки
        """
        # Валидация данных
        valid_notifications = []
        for notification in notifications:
            if self._validate_notification(notification):
                # Стандартизация формата времени
                notification["time"] = self._normalize_time_format(notification["time"])
                valid_notifications.append(notification)
            else:
                logger.warning(f"Пропущено некорректное уведомление для пользователя {user_id}: {notification}")
        
        if not valid_notifications:
            logger.error(f"Нет корректных уведомлений для замены для пользователя {user_id}")
            return False
        
        user_id_str = str(user_id)
        
        logger.info(f"Замена настроек уведомлений для пользователя {user_id}")
        logger.info(f"  Старое количество уведомлений: {len(self.user_notifications.get(user_id_str, []))}")
        logger.info(f"  Новое количество уведомлений: {len(valid_notifications)}")
        
        # Полная замена настроек
        self.user_notifications[user_id_str] = valid_notifications
        
        # Сохранение изменений
        success = self._save_notifications()
        
        if success:
            logger.info(f"Настройки уведомлений для пользователя {user_id} успешно заменены")
            
            # Сброс отслеживания отправленных данных для пользователя
            if user_id in self.sent_events:
                del self.sent_events[user_id]
            if user_id in self.sent_figures:
                del self.sent_figures[user_id]
        
        return success
    
    def remove_user_notification(self, user_id: int, notification_time: str) -> bool:
        """
        Удаление настройки уведомления для пользователя
        
        Args:
            user_id: ID пользователя
            notification_time: Время уведомления
            
        Returns:
            True, если уведомление было удалено, False в противном случае
        """
        user_id_str = str(user_id)
        
        if user_id_str not in self.user_notifications:
            logger.warning(f"Попытка удаления уведомления для несуществующего пользователя {user_id}")
            return False
        
        # Стандартизация формата времени
        notification_time = self._normalize_time_format(notification_time)
        
        # Поиск и удаление настройки с указанным временем
        original_length = len(self.user_notifications[user_id_str])
        self.user_notifications[user_id_str] = [
            n for n in self.user_notifications[user_id_str]
            if n["time"] != notification_time
        ]
        
        # Проверка, было ли что-то удалено
        was_removed = len(self.user_notifications[user_id_str]) < original_length
        
        # Сохранение изменений, если что-то было удалено
        if was_removed:
            success = self._save_notifications()
            if success:
                logger.info(f"Удалено уведомление для пользователя {user_id} на время {notification_time}")
            return success
        else:
            logger.warning(f"Уведомление на время {notification_time} не найдено для пользователя {user_id}")
            return False
    
    def get_user_notifications(self, user_id: int) -> List[Dict]:
        """
        Получение всех настроек уведомлений для пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список настроек уведомлений
        """
        user_id_str = str(user_id)
        
        if user_id_str not in self.user_notifications:
            logger.debug(f"Запрошены уведомления для несуществующего пользователя {user_id}")
            return []
        
        return self.user_notifications[user_id_str]
    
    def set_user_timezone(self, user_id: int, timezone_offset: int) -> None:
        """
        Установка часового пояса пользователя
        
        Args:
            user_id: ID пользователя
            timezone_offset: Смещение часового пояса в часах относительно UTC
        """
        self.user_timezones[user_id] = timezone_offset
        logger.info(f"Установлен часовой пояс {timezone_offset} для пользователя {user_id}")
    
    async def schedule_notifications(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Планирование отправки уведомлений для всех пользователей
        
        Args:
            context: Контекст Telegram-бота
        """
        # Удаление всех существующих запланированных задач
        current_jobs = context.job_queue.get_jobs_by_name("notification")
        if current_jobs:
            for job in current_jobs:
                job.schedule_removal()
            logger.info(f"Удалено {len(current_jobs)} существующих задач уведомлений")
        
        # Подсчет запланированных уведомлений
        total_scheduled = 0
        
        # Планирование новых задач для каждого пользователя и времени
        for user_id_str, notifications in self.user_notifications.items():
            user_id = int(user_id_str)
            
            for notification in notifications:
                try:
                    # Стандартизация формата времени
                    time_str = self._normalize_time_format(notification["time"])
                    
                    # Разбиение времени на часы и минуты
                    time_parts = time_str.split(":")
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    
                    # Создание времени для запуска
                    time_to_run = datetime.time(hour=hour, minute=minute)
                    
                    # Получение часового пояса пользователя (если установлен)
                    timezone_offset = self.user_timezones.get(user_id, 0)
                    
                    # Корректировка времени с учетом часового пояса
                    if timezone_offset != 0:
                        # Преобразование в datetime для применения смещения
                        now = datetime.datetime.now()
                        target_datetime = datetime.datetime.combine(now.date(), time_to_run)
                        
                        # Применение смещения
                        target_datetime -= datetime.timedelta(hours=timezone_offset)
                        
                        # Если получилось отрицательное время, добавляем день
                        if target_datetime.day != now.day:
                            if target_datetime < now:
                                target_datetime += datetime.timedelta(days=1)
                            else:
                                target_datetime -= datetime.timedelta(days=1)
                        
                        # Обновление времени для запуска
                        time_to_run = target_datetime.time()
                    
                    # Создание потенциального времени запуска на сегодня
                    now = datetime.datetime.now()
                    target_time = datetime.datetime.combine(
                        now.date(),
                        time_to_run
                    )
                    
                    # Если время уже прошло, планируем на завтра
                    if target_time <= now:
                        target_time += datetime.timedelta(days=1)
                        logger.debug(f"Время {hour}:{minute:02d} уже прошло, планирование на завтра")
                    
                    # Расчет задержки до запуска (для отладки)
                    time_diff = target_time - now
                    hours_until = time_diff.total_seconds() / 3600
                    
                    logger.debug(f"Планирование на {hour}:{minute:02d}, задержка: {hours_until:.2f} часов")
                    
                    # Планирование задачи через run_daily
                    context.job_queue.run_daily(
                        self._send_notification,
                        time=time_to_run,
                        data={
                            "user_id": user_id,
                            "notification": notification
                        },
                        name="notification"
                    )
                    
                    total_scheduled += 1
                    logger.info(f"Запланировано уведомление для пользователя {user_id} на {hour}:{minute:02d}")
                
                except Exception as e:
                    logger.error(f"Ошибка при планировании уведомления: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
        
        logger.info(f"Всего запланировано {total_scheduled} уведомлений")
    
    def _should_send_notification(self, user_id: int, notification_time: str) -> bool:
        """
        Проверка, нужно ли отправлять уведомление
        
        Args:
            user_id: ID пользователя
            notification_time: Время уведомления
            
        Returns:
            True, если уведомление нужно отправить, False в противном случае
        """
        current_time = datetime.datetime.now()
        
        # Инициализация отслеживания для пользователя, если его еще нет
        if user_id not in self.last_send_time:
            self.last_send_time[user_id] = {}
        
        # Получение времени последней отправки для данного уведомления
        last_send = self.last_send_time[user_id].get(notification_time)
        
        if last_send is None:
            # Если уведомление еще не отправлялось
            return True
        
        # Преобразование timestamp в datetime
        last_send_datetime = datetime.datetime.fromtimestamp(last_send)
        
        # Проверка, прошло ли достаточно времени с последней отправки
        time_diff = current_time - last_send_datetime
        
        # Минимальный интервал между отправками - 12 часов
        min_interval = datetime.timedelta(hours=12)
        
        return time_diff >= min_interval
    
    def _update_last_send_time(self, user_id: int, notification_time: str) -> None:
        """
        Обновление времени последней отправки уведомления
        
        Args:
            user_id: ID пользователя
            notification_time: Время уведомления
        """
        current_timestamp = int(datetime.datetime.now().timestamp())
        
        # Инициализация отслеживания для пользователя, если его еще нет
        if user_id not in self.last_send_time:
            self.last_send_time[user_id] = {}
        
        # Обновление времени последней отправки
        self.last_send_time[user_id][notification_time] = current_timestamp
        
        logger.debug(f"Обновлено время последней отправки для пользователя {user_id} и времени {notification_time}")
    
    async def _send_notification(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Отправка уведомления пользователю
        
        Args:
            context: Контекст Telegram-бота
        """
        try:
            job_data = context.job.data
            user_id = job_data["user_id"]
            notification = job_data["notification"]
            time_str = notification["time"]
            
            logger.info(f"Подготовка уведомления для пользователя {user_id} на время {time_str}")
            
            # Проверка, нужно ли отправлять уведомление
            if not self._should_send_notification(user_id, time_str):
                logger.info(f"Пропуск отправки уведомления для пользователя {user_id} на время {time_str} (слишком рано)")
                return
            
            # Получение количества событий и деятелей для отправки
            events_count = notification.get("events_count", 0)
            figures_count = notification.get("figures_count", 0)
                
            # Инициализация отслеживания для пользователя, если его еще нет
            if user_id not in self.sent_events:
                self.sent_events[user_id] = set()
            if user_id not in self.sent_figures:
                self.sent_figures[user_id] = set()
            
            # Подготовка материалов для отправки
            events_to_send = self._get_events_for_notification(user_id, events_count)
            figures_to_send = self._get_figures_for_notification(user_id, figures_count)
            
            # Если нет материалов для отправки, отменяем отправку
            if not events_to_send and not figures_to_send:
                logger.warning(f"Нет материалов для отправки пользователю {user_id}")
                return
            
            # Формирование сообщения для отправки
            message = self._format_notification_message(events_to_send, figures_to_send)
            
            # Отправка сообщения пользователю
            logger.info(f"Отправка уведомления пользователю {user_id}")
            
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown"
            )
            
            # Обновление времени последней отправки
            self._update_last_send_time(user_id, time_str)
            
            logger.info(f"Уведомление успешно отправлено пользователю {user_id}")
        
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _get_events_for_notification(self, user_id: int, count: int) -> List[Dict]:
        """
        Получение событий для уведомления
        
        Args:
            user_id: ID пользователя
            count: Количество событий
            
        Returns:
            Список событий для отправки
        """
        if count <= 0:
            return []
        
        # Получение всех доступных событий
        all_events = self.data_manager.get_all_events()
        
        if not all_events:
            logger.warning("База данных не содержит событий")
            return []
        
        # Определение, какие события еще не были отправлены
        unsent_events = [
            event for event in all_events
            if event["id"] not in self.sent_events[user_id]
        ]
        
        # Если все события уже были отправлены или их недостаточно, начинаем заново
        if not unsent_events or len(unsent_events) < count:
            logger.info(f"Сброс счетчика отправленных событий для пользователя {user_id}")
            self.sent_events[user_id] = set()
            unsent_events = all_events
        
        # Выбор случайных событий для отправки
        random.shuffle(unsent_events)
        events_to_send = unsent_events[:count]
        
        # Отметка отправленных событий
        for event in events_to_send:
            self.sent_events[user_id].add(event["id"])
        
        logger.debug(f"Подготовлено {len(events_to_send)} событий для пользователя {user_id}")
        return events_to_send
    
    def _get_figures_for_notification(self, user_id: int, count: int) -> List[Dict]:
        """
        Получение деятелей для уведомления
        
        Args:
            user_id: ID пользователя
            count: Количество деятелей
            
        Returns:
            Список деятелей для отправки
        """
        if count <= 0:
            return []
        
        # Получение всех доступных деятелей
        all_figures = self.data_manager.get_all_figures()
        
        if not all_figures:
            logger.warning("База данных не содержит деятелей")
            return []
        
        # Определение, какие деятели еще не были отправлены
        unsent_figures = [
            figure for figure in all_figures
            if figure["id"] not in self.sent_figures[user_id]
        ]
        
        # Если все деятели уже были отправлены или их недостаточно, начинаем заново
        if not unsent_figures or len(unsent_figures) < count:
            logger.info(f"Сброс счетчика отправленных деятелей для пользователя {user_id}")
            self.sent_figures[user_id] = set()
            unsent_figures = all_figures
        
        # Выбор случайных деятелей для отправки
        random.shuffle(unsent_figures)
        figures_to_send = unsent_figures[:count]
        
        # Отметка отправленных деятелей
        for figure in figures_to_send:
            self.sent_figures[user_id].add(figure["id"])
        
        logger.debug(f"Подготовлено {len(figures_to_send)} деятелей для пользователя {user_id}")
        return figures_to_send
    
    def _format_notification_message(self, events: List[Dict], figures: List[Dict]) -> str:
        """
        Форматирование сообщения с учебными материалами
        
        Args:
            events: Список событий
            figures: Список деятелей
            
        Returns:
            Отформатированное сообщение
        """
        message = f"📚 *Ваши материалы для изучения:*\n\n"
        
        if events:
            message += "*Исторические события:*\n"
            for i, event in enumerate(events, 1):
                message += f"{i}. 📅 *{event['date']}*: {event['description']}\n\n"
        
        if figures:
            message += "*Исторические деятели:*\n"
            for i, figure in enumerate(figures, 1):
                message += f"{i}. 👤 *{figure['name']}*: {figure['achievement']}\n\n"
        
        # Добавляем случайный совет по изучению
        message += self._get_random_study_tip()
        
        return message
    
    def _get_random_study_tip(self) -> str:
        """
        Получение случайного совета по изучению
        
        Returns:
            Случайный совет
        """
        tips = [
            "💡 *Совет:* Используйте мнемонические техники для запоминания дат и имен.",
            "💡 *Совет:* Для лучшего запоминания объясните материал другому человеку своими словами.",
            "💡 *Совет:* Регулярно проходите тесты для закрепления изученного материала.",
            "💡 *Совет:* Связывайте новую информацию с уже известными вам фактами.",
            "💡 *Совет:* Создавайте ассоциации между историческими личностями и их достижениями.",
            "💡 *Совет:* Группируйте события по историческим периодам для лучшего понимания контекста.",
            "💡 *Совет:* Составляйте временные линии для визуализации последовательности событий.",
            "💡 *Совет:* Используйте режим 'Марафон' для комплексной проверки знаний.",
            "💡 *Совет:* Прохождение тестов разных типов помогает лучше усвоить материал.",
            "💡 *Совет:* Регулярное повторение - ключ к долговременному запоминанию."
        ]
        
        return f"\n{random.choice(tips)}"