import logging
import re
import os
import time
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, error
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters


from data_manager import DataManager
from notifications import NotificationManager
from knowledge_test import KnowledgeTest
from stats_manager import StatsManager
import datetime

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация менеджеров
data_manager = DataManager("history_data.json")
notification_manager = NotificationManager(data_manager)
knowledge_test = KnowledgeTest(data_manager)
stats_manager = StatsManager()

# Обработчики команд и клавиатуры
def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Создает улучшенную основную клавиатуру быстрого доступа"""
    keyboard = [
        [KeyboardButton("📚 Проверка знаний"), KeyboardButton("🏆 Марафон")],
        [KeyboardButton("📊 Статистика"), KeyboardButton("➕ Добавить данные")],
        [KeyboardButton("⚙️ Настройки обучения"), KeyboardButton("❓ Справка")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_state_keyboard(state: str = None) -> ReplyKeyboardMarkup:
    """Создает клавиатуру в зависимости от текущего состояния"""
    
    if state and state not in ["main_menu", None]:
        keyboard = [
            [KeyboardButton("❌ Отменить действие"), KeyboardButton("❓ Справка")]
        ]
    else:
        keyboard = [
            [KeyboardButton("📚 Проверка знаний"), KeyboardButton("🏆 Марафон")],
            [KeyboardButton("📊 Статистика"), KeyboardButton("➕ Добавить данные")],
            [KeyboardButton("⚙️ Настройки обучения"), KeyboardButton("❓ Справка")]
        ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Функция запуска бота с подробными инструкциями"""
    # Инициализируем базу данных примерами, если она пуста
    data_manager.initialize_sample_data()
    
    # Создаем reply клавиатуру для быстрого доступа
    main_keyboard = get_main_keyboard()
    
    # Создаем inline клавиатуру для первоначальной навигации
    inline_keyboard = [
        [InlineKeyboardButton("📚 Проверка знаний", callback_data="testing")],
        [InlineKeyboardButton("🏆 Марафон", callback_data="start_marathon")],
        [InlineKeyboardButton("📊 Статистика", callback_data="statistics")],
        [InlineKeyboardButton("➕ Добавить данные", callback_data="add_data")],
        [InlineKeyboardButton("⚙️ Настройки обучения", callback_data="learning")],
        [InlineKeyboardButton("❓ Справка", callback_data="help_main")]
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)
    
    # Улучшенное приветственное сообщение с инструкциями
    welcome_message = (
        "👋 *Приветствую вас в боте для подготовки к экзамену по истории Беларуси!*\n\n"
        
        "🤖 *Возможности бота:*\n"
        "• 📚 Тестирование знаний по датам, событиям и историческим деятелям\n"
        "• 🏆 Марафон для комплексной проверки знаний\n"
        "• 📊 Отслеживание прогресса и персональные рекомендации\n"
        "• ⏰ Регулярная отправка учебных материалов\n"
        "• ➕ Добавление собственных данных в базу\n\n"
        
        "🚀 *Начало работы:*\n"
        "1️⃣ Настройте уведомления в 'Настройки обучения'\n"
        "2️⃣ Проверьте свои знания в 'Проверка знаний'\n"
        "3️⃣ Пройдите 'Марафон' для комплексной подготовки\n"
        "4️⃣ Следите за прогрессом в 'Статистика'\n\n"
        
        "Выберите режим или используйте кнопки быстрого доступа:"
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=inline_markup,
        parse_mode="Markdown"
    )
    
    # Отправляем второе сообщение с напоминанием о режиме обучения
    await update.message.reply_text(
        "ℹ️ *Важно о режиме обучения:* После настройки бот будет регулярно отправлять вам учебные материалы "
        "по выбранному расписанию. Это позволит эффективно изучать историю даже в интенсивном режиме подготовки.\n\n"
        "Чтобы начать, нажмите '⚙️ Настройки обучения'.",
        parse_mode="Markdown",
        reply_markup=main_keyboard
    )

# Централизованная обработка справки
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /help с расширенной информацией о боте"""
    # Создаем интерактивное меню помощи с разделами
    keyboard = [
        [InlineKeyboardButton("📚 Как проходить тесты", callback_data="help_testing")],
        [InlineKeyboardButton("🏆 Как играть в марафон", callback_data="help_marathon")],
        [InlineKeyboardButton("⚙️ Настройка уведомлений", callback_data="help_notifications")],
        [InlineKeyboardButton("📊 Работа со статистикой", callback_data="help_statistics")],
        [InlineKeyboardButton("➕ Добавление данных", callback_data="help_add_data")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    help_text = (
        "🤖 *Помощник по истории Беларуси*\n\n"
        "Этот бот создан, чтобы помочь вам эффективно подготовиться к экзамену. "
        "Выберите интересующий раздел помощи:\n\n"
        
        "📚 *Основные команды:*\n"
        "/start - Запустить бота\n"
        "/help - Показать справку\n"
        "/cancel - Отменить текущее действие\n"
        "/test_notification - Получить тестовое уведомление\n"
        "/check_jobs - Проверить запланированные уведомления\n\n"
        
        "Используйте кнопки ниже для получения подробной информации."
    )
    
    await update.message.reply_text(
        help_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# Раздел обработки справки по разделам
async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка запросов о помощи и показ соответствующих инструкций"""
    query = update.callback_query
    await query.answer()
    
    # Кнопка "Назад к справке" для всех разделов
    back_button = [InlineKeyboardButton("🔙 Назад к справке", callback_data="help_main")]
    
    if query.data == "help_main":
        # Возвращаемся к главному меню помощи
        return await help_command(update, context)
    
    elif query.data == "help_testing":
        # Инструкции по тестированию
        keyboard = [
            [InlineKeyboardButton("По дате", callback_data="help_test_date")],
            [InlineKeyboardButton("По событию", callback_data="help_test_event")],
            [InlineKeyboardButton("По деятелю", callback_data="help_test_figure")],
            [InlineKeyboardButton("По достижению", callback_data="help_test_achievement")],
            back_button[0]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            "📚 *Режим тестирования*\n\n"
            "В боте доступны 4 типа тестов для комплексной проверки знаний:\n\n"
            
            "1️⃣ *По дате* — показывается дата, нужно указать событие\n"
            "2️⃣ *По событию* — показывается событие, нужно указать дату\n"
            "3️⃣ *По деятелю* — показывается имя, нужно указать достижения\n"
            "4️⃣ *По достижению* — показывается достижение, нужно указать имя\n\n"
            
            "Выберите тип теста для получения подробных инструкций."
        )
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    elif query.data.startswith("help_test_"):
        # Подробные инструкции по конкретному типу теста
        test_type = query.data.replace("help_test_", "")
        reply_markup = InlineKeyboardMarkup([back_button])
        
        if test_type == "date":
            message = (
                "📅 *Тестирование по дате*\n\n"
                "В этом режиме вам показывается историческая дата, например: *1569*\n\n"
                "Ваша задача — написать событие, которое произошло в эту дату.\n"
                "Например: *Люблинская уния. Объединение ВКЛ и Польского королевства*\n\n"
                
                "📝 *Как отвечать:*\n"
                "• Система распознает близкие по смыслу ответы\n"
                "• Старайтесь использовать ключевые термины\n"
                "• Ответ может быть кратким, но информативным\n\n"
                
                "💡 *Совет:* Регулярно просматривайте карточки с датами в режиме обучения."
            )
        elif test_type == "event":
            message = (
                "🔍 *Тестирование по событию*\n\n"
                "В этом режиме вам показывается историческое событие, например:\n"
                "*Люблинская уния. Объединение ВКЛ и Польского королевства*\n\n"
                
                "Ваша задача — указать дату, когда произошло это событие (например: *1569*)\n\n"
                
                "📝 *Как отвечать:*\n"
                "• Для точных дат укажите год (1569)\n"
                "• Для периодов укажите диапазон (1863-1864)\n"
                "• Для некоторых событий может потребоваться полная дата\n\n"
                
                "💡 *Совет:* Составьте хронологическую таблицу ключевых событий."
            )
        elif test_type == "figure":
            message = (
                "👤 *Тестирование по историческому деятелю*\n\n"
                "В этом режиме вам показывается имя исторического деятеля, например:\n"
                "*Франциск Скорина*\n\n"
                
                "Ваша задача — описать его достижения, например:\n"
                "*Белорусский первопечатник, переводчик Библии на старобелорусский язык*\n\n"
                
                "📝 *Как отвечать:*\n"
                "• Укажите основные достижения или вклад в историю\n"
                "• Система распознает близкие по смыслу формулировки\n"
                "• Включайте годы жизни или периоды деятельности\n\n"
                
                "💡 *Совет:* Группируйте исторических деятелей по эпохам."
            )
        elif test_type == "achievement":
            message = (
                "🏆 *Тестирование по достижению*\n\n"
                "В этом режиме вам показывается достижение, например:\n"
                "*Белорусский первопечатник, переводчик Библии на старобелорусский язык*\n\n"
                
                "Ваша задача — назвать исторического деятеля, например:\n"
                "*Франциск Скорина*\n\n"
                
                "📝 *Как отвечать:*\n"
                "• Укажите полное имя исторического деятеля\n"
                "• Обратите внимание на правильное написание\n"
                "• Система учитывает распространенные варианты написания\n\n"
                
                "💡 *Совет:* Создайте карточки с достижениями и именами для тренировки."
            )
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    elif query.data == "help_marathon":
        # Инструкции по марафону
        reply_markup = InlineKeyboardMarkup([back_button])
        
        message = (
            "🏆 *Марафон знаний*\n\n"
            "Марафон — это серия из 5 вопросов разных типов, которые нужно пройти последовательно. "
            "Это эффективный способ комплексной проверки знаний.\n\n"
            
            "📝 *Как работает марафон:*\n"
            "1. Нажмите кнопку '🏆 Марафон'\n"
            "2. Вам будет показан вопрос одного из четырех типов\n"
            "3. После ответа нажмите 'Следующий вопрос'\n"
            "4. После всех вопросов вы увидите итоговый результат\n\n"
            
            "🔄 *Особенности:*\n"
            "• Вопросы выбираются случайно из всех категорий\n"
            "• Нельзя пропустить вопрос или вернуться назад\n"
            "• Результаты влияют на вашу общую статистику\n\n"
            
            "💡 *Совет:* Проходите марафон ежедневно для отслеживания прогресса."
        )
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    elif query.data == "help_notifications":
        # Инструкции по настройке уведомлений
        reply_markup = InlineKeyboardMarkup([back_button])
        
        message = (
            "⚙️ *Настройка режима обучения*\n\n"
            "Режим обучения позволяет получать регулярные уведомления с историческим материалом "
            "для систематического изучения и повторения.\n\n"
            
            "📝 *Пошаговая настройка:*\n"
            "1. Выберите количество уведомлений в день (1-10)\n"
            "2. Для каждого уведомления задайте:\n"
            "   • Время отправки (формат ЧЧ:ММ, например 09:00)\n"
            "   • Количество исторических событий\n"
            "   • Количество исторических деятелей\n\n"
            
            "🔄 *Управление уведомлениями:*\n"
            "• Для изменения настроек просто запустите настройку заново\n"
            "• Команда /check_jobs покажет статус уведомлений\n"
            "• Команда /test_notification отправит тестовое уведомление\n\n"
            
            "💡 *Совет:* Распределите уведомления равномерно в течение дня."
        )
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    elif query.data == "help_statistics":
        # Инструкции по работе со статистикой
        reply_markup = InlineKeyboardMarkup([back_button])
        
        message = (
            "📊 *Статистика обучения*\n\n"
            "Статистика помогает отслеживать прогресс и выявлять области, требующие внимания.\n\n"
            
            "📈 *Доступная информация:*\n"
            "• Общее количество пройденных тестов\n"
            "• Процент правильных ответов (общий и по типам)\n"
            "• Сложные для вас вопросы и темы\n"
            "• Недавние ошибки для повторения\n"
            "• Персональные рекомендации\n\n"
            
            "📝 *Как использовать:*\n"
            "1. Регулярно проверяйте статистику для оценки прогресса\n"
            "2. Обращайте внимание на сложные вопросы\n"
            "3. Используйте раздел рекомендаций для улучшения результатов\n\n"
            
            "💡 *Совет:* Составляйте план повторения на основе статистики."
        )
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    elif query.data == "help_add_data":
        # Инструкции по добавлению данных
        reply_markup = InlineKeyboardMarkup([back_button])
        
        message = (
            "➕ *Добавление собственных данных*\n\n"
            "Вы можете расширить базу данных бота, добавляя свои события и деятелей.\n\n"
            
            "📝 *Добавление события:*\n"
            "1. Выберите '➕ Добавить данные' → 'Добавить событие'\n"
            "2. Введите дату в любом формате (1569, 1941-1944, 27 июля 1990)\n"
            "3. Введите полное описание события\n\n"
            
            "👤 *Добавление деятеля:*\n"
            "1. Выберите '➕ Добавить данные' → 'Добавить деятеля'\n"
            "2. Введите полное имя исторического деятеля\n"
            "3. Введите описание его достижений или вклада\n\n"
            
            "🔄 *Важная информация:*\n"
            "• Добавленные данные будут использоваться в тестах и уведомлениях\n"
            "• Используйте точные и информативные формулировки\n\n"
            
            "💡 *Совет:* Добавляйте данные из официальных учебных материалов."
        )
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# Контекстная помощь в зависимости от состояния пользователя
async def show_context_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отображает справку в зависимости от текущего состояния пользователя"""
    state = context.user_data.get("state")
    
    if state is None or state == "main_menu":
        await help_command(update, context)
        return
    
    # Справка по текущему состоянию
    help_data = ""
    if state == "testing":
        test_type = context.user_data.get("test_type")
        help_data = f"help_test_{test_type}" if test_type else "help_testing"
    elif state == "marathon":
        help_data = "help_marathon"
    elif state in ["setting_notifications_count", "setting_notification_time", "setting_events_count", "setting_figures_count"]:
        help_data = "help_notifications"
    elif state in ["adding_event_date", "adding_event_description", "adding_figure_name", "adding_figure_achievement"]:
        help_data = "help_add_data"
    else:
        await help_command(update, context)
        return
    
    # Создаем контекст для эмуляции callback
    context.user_data["emulated_callback"] = help_data
    
    # Создаем объект-заглушку для эмуляции callback_query
    class DummyQuery:
        def __init__(self, data):
            self.data = data
        
        async def answer(self):
            pass
        
        async def edit_message_text(self, **kwargs):
            # Отправляем сообщение вместо редактирования
            await update.message.reply_text(
                kwargs.get("text", ""),
                reply_markup=kwargs.get("reply_markup"),
                parse_mode=kwargs.get("parse_mode")
            )
    
    # Создаем фиктивную копию update с нашим dummy query
    update_copy = update
    update_copy.callback_query = DummyQuery(help_data)
    
    # Вызываем обработчик справки
    await help_callback(update_copy, context)

# Улучшенный показ результатов тестов
async def finish_test_with_tips(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                               is_correct: bool, test_type: str, 
                               question: str, answer: str) -> None:
    """Показывает результат теста с дополнительными советами по обучению"""
    # Базовое сообщение с результатом
    result_message = "✅ Правильно!" if is_correct else "❌ Неправильно."
    result_message += f"\n\nПравильный ответ: *{answer}*\n\n"
    
    # Добавляем специфичные советы в зависимости от типа теста и результата
    if not is_correct:
        if test_type == "date":
            result_message += "💡 *Совет:* Составьте хронологическую таблицу событий и повторяйте её регулярно."
        elif test_type == "event":
            result_message += "💡 *Совет:* Связывайте события с историческим контекстом эпохи для лучшего запоминания."
        elif test_type == "figure":
            result_message += "💡 *Совет:* Группируйте исторических деятелей по периодам или направлениям деятельности."
        elif test_type == "achievement":
            result_message += "💡 *Совет:* Создайте карточки с достижениями и именами для эффективного запоминания."
    
    # Кнопки для продолжения
    keyboard = [
        [InlineKeyboardButton("Продолжить тестирование", callback_data="continue_testing")],
        [InlineKeyboardButton("Показать статистику", callback_data="statistics")],
        [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        result_message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# Основной обработчик callback-кнопок
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка всех callback-кнопок интерфейса"""
    query = update.callback_query
    await query.answer()
    
    # Распределение обработки по типам callback
    if query.data == "learning":
        await start_learning(update, context)
    elif query.data == "testing":
        await start_testing(update, context)
    elif query.data == "add_data":
        await start_adding_data(update, context)
    elif query.data == "main_menu":
        await show_main_menu(update, context)
    elif query.data == "start_marathon":
        await start_marathon_callback(update, context)
    elif query.data == "next_marathon_question":
        await next_marathon_question_callback(update, context)
    elif query.data == "statistics":
        await show_statistics(update, context)
    elif query.data == "test_date":
        context.user_data["state"] = "testing"
        context.user_data["test_type"] = "date"
        await knowledge_test.start_date_test(update, context)
    elif query.data == "test_event":
        context.user_data["state"] = "testing"
        context.user_data["test_type"] = "event"
        await knowledge_test.start_event_test(update, context)
    elif query.data == "test_figure":
        context.user_data["state"] = "testing"
        context.user_data["test_type"] = "figure"
        await knowledge_test.start_figure_test(update, context)
    elif query.data == "test_achievement":
        context.user_data["state"] = "testing"
        context.user_data["test_type"] = "achievement"
        await knowledge_test.start_achievement_test(update, context)
    elif query.data == "continue_testing":
        await continue_testing(update, context)
    elif query.data == "add_event":
        await add_event_start(update, context)
    elif query.data == "add_figure":
        await add_figure_start(update, context)

# Отображение главного меню
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отображает главное меню с основными функциями"""
    keyboard = [
        [InlineKeyboardButton("📚 Проверка знаний", callback_data="testing")],
        [InlineKeyboardButton("🏆 Марафон", callback_data="start_marathon")],
        [InlineKeyboardButton("📊 Статистика", callback_data="statistics")],
        [InlineKeyboardButton("➕ Добавить данные", callback_data="add_data")],
        [InlineKeyboardButton("⚙️ Настройки обучения", callback_data="learning")],
        [InlineKeyboardButton("❓ Справка", callback_data="help_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Напоминаем о кнопках быстрого доступа
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🔍 *Главное меню*\n\n"
            "Выберите нужный режим работы:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🔍 *Главное меню*\n\n"
            "Выберите нужный режим работы:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Убедимся, что пользователь имеет доступ к reply keyboard
    main_keyboard = get_main_keyboard()
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text="Используйте эти кнопки для быстрого доступа:",
        reply_markup=main_keyboard
    )
    
    # Сбрасываем состояние
    context.user_data["state"] = "main_menu"

# Функции для режима обучения
async def start_learning(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало настройки режима обучения"""
    context.user_data["state"] = "setting_notifications_count"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "⚙️ *Настройка режима обучения*\n\n"
            "Сколько уведомлений в день вы хотите получать? (Введите число от 1 до 10)\n\n"
            "💡 *Совет:* Оптимально 3-5 уведомлений, распределенных в течение дня.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "⚙️ *Настройка режима обучения*\n\n"
            "Сколько уведомлений в день вы хотите получать? (Введите число от 1 до 10)\n\n"
            "💡 *Совет:* Оптимально 3-5 уведомлений, распределенных в течение дня.",
            parse_mode="Markdown"
        )
    
    # Отправляем клавиатуру с кнопкой отмены
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text="Используйте кнопки ниже для управления:",
        reply_markup=get_state_keyboard(context.user_data["state"])
    )

# Обработчики для настройки уведомлений
async def handle_notification_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка ввода количества уведомлений"""
    try:
        notifications_count = int(update.message.text)
        if notifications_count < 1 or notifications_count > 10:
            await update.message.reply_text(
                "⚠️ Пожалуйста, введите число от 1 до 10.",
                reply_markup=get_state_keyboard(context.user_data["state"])
            )
            return
        
        context.user_data["notifications_count"] = notifications_count
        context.user_data["current_notification"] = 1
        context.user_data["notifications"] = []
        context.user_data["state"] = "setting_notification_time"
        
        await update.message.reply_text(
            f"✅ Количество уведомлений ({notifications_count}) сохранено.\n\n"
            f"📝 Настраиваем уведомление 1 из {notifications_count}.\n"
            f"Введите время для этого уведомления в формате ЧЧ:ММ (например, 09:00)\n\n"
            f"💡 *Совет:* Выбирайте время, когда вы можете уделить 5-10 минут на изучение материала.",
            parse_mode="Markdown",
            reply_markup=get_state_keyboard(context.user_data["state"])
        )
    except ValueError:
        await update.message.reply_text(
            "⚠️ Пожалуйста, введите корректное число.",
            reply_markup=get_state_keyboard(context.user_data["state"])
        )

async def handle_notification_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка ввода времени уведомления"""
    time_text = update.message.text
    
    # Проверка формата времени
    if not re.match(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$", time_text):
        await update.message.reply_text(
            "⚠️ Неверный формат времени. Введите время в формате ЧЧ:ММ (например, 09:00)",
            reply_markup=get_state_keyboard(context.user_data["state"])
        )
        return
    
    # Создание новой записи для уведомления
    notification = {
        "time": time_text,
        "events_count": 0,
        "figures_count": 0
    }
    
    # Добавление уведомления в список
    context.user_data["notifications"].append(notification)
    
    # Переход к настройке контента
    context.user_data["state"] = "setting_events_count"
    
    await update.message.reply_text(
        f"✅ Время уведомления {time_text} сохранено.\n\n"
        f"Сколько исторических событий с датами вы хотите получать в это время? (Введите число)\n\n"
        f"💡 *Совет:* Рекомендуется 2-3 события за один раз для лучшего запоминания.",
        parse_mode="Markdown",
        reply_markup=get_state_keyboard(context.user_data["state"])
    )

async def handle_events_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка ввода количества событий"""
    try:
        events_count = int(update.message.text)
        if events_count < 0:
            await update.message.reply_text(
                "⚠️ Пожалуйста, введите неотрицательное число.",
                reply_markup=get_state_keyboard(context.user_data["state"])
            )
            return
        
        # Сохранение количества событий
        context.user_data["notifications"][-1]["events_count"] = events_count
        
        # Обновляем состояние
        context.user_data["state"] = "setting_figures_count"
        
        await update.message.reply_text(
            f"✅ Количество событий ({events_count}) сохранено.\n\n"
            f"Сколько исторических деятелей вы хотите получать в это время? (Введите число)\n\n"
            f"💡 *Совет:* Рекомендуется 1-2 исторических деятеля за один раз.",
            parse_mode="Markdown",
            reply_markup=get_state_keyboard(context.user_data["state"])
        )
    except ValueError:
        await update.message.reply_text(
            "⚠️ Пожалуйста, введите корректное число.",
            reply_markup=get_state_keyboard(context.user_data["state"])
        )

async def handle_figures_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка ввода количества деятелей"""
    try:
        figures_count = int(update.message.text)
        if figures_count < 0:
            await update.message.reply_text(
                "⚠️ Пожалуйста, введите неотрицательное число.",
                reply_markup=get_state_keyboard(context.user_data["state"])
            )
            return
        
        # Сохранение количества деятелей
        current_notification = context.user_data["current_notification"]
        notifications_count = context.user_data["notifications_count"]
        context.user_data["notifications"][-1]["figures_count"] = figures_count
        
        # Переход к следующему уведомлению или завершение настройки
        if current_notification < notifications_count:
            context.user_data["current_notification"] += 1
            context.user_data["state"] = "setting_notification_time"
            
            await update.message.reply_text(
                f"✅ Количество деятелей ({figures_count}) сохранено.\n\n"
                f"📝 Настраиваем уведомление {current_notification + 1} из {notifications_count}.\n"
                f"Введите время для этого уведомления в формате ЧЧ:ММ (например, 09:00)",
                reply_markup=get_state_keyboard(context.user_data["state"])
            )
        else:
            # Завершение настройки
            await finalize_notifications_setup(update, context)
    except ValueError:
        await update.message.reply_text(
            "⚠️ Пожалуйста, введите корректное число.",
            reply_markup=get_state_keyboard(context.user_data["state"])
        )

async def finalize_notifications_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Завершение настройки уведомлений и сохранение результатов"""
    user_id = update.effective_user.id
    notifications = context.user_data["notifications"]
    
    # Замена всех уведомлений пользователя
    notification_manager.replace_all_user_notifications(user_id, notifications)
    
    # Планирование уведомлений
    await notification_manager.schedule_notifications(context)
    
    # Формирование краткого описания настроек
    notification_summary = "✅ *Настройки режима обучения сохранены!*\n\n"
    notification_summary += "📣 *Ваши уведомления:*\n\n"
    
    for i, notification in enumerate(notifications, 1):
        notification_summary += (
            f"*Уведомление {i}:* `{notification['time']}` – "
            f"{notification['events_count']} событий, "
            f"{notification['figures_count']} деятелей\n"
        )
    
    notification_summary += "\n✅ *Режим обучения активирован!*\n"
    notification_summary += "Вы будете получать материалы по указанному расписанию.\n\n"
    notification_summary += "💡 *Команды управления:*\n"
    notification_summary += "• /check_jobs – проверить запланированные уведомления\n"
    notification_summary += "• /test_notification – получить тестовое уведомление"
    
    keyboard = [
        [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
    ]
    inline_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        notification_summary, 
        reply_markup=inline_markup,
        parse_mode="Markdown"
    )
    
    # Возвращаем основную клавиатуру
    main_keyboard = get_main_keyboard()
    await update.message.reply_text(
        "Используйте кнопки быстрого доступа для работы с ботом:",
        reply_markup=main_keyboard
    )
    
    context.user_data["state"] = None

async def test_notification_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправка тестового уведомления для проверки настроек"""
    user_id = update.effective_user.id
    
    await update.message.reply_text(
        "⏳ Отправка тестового уведомления...",
        reply_markup=get_main_keyboard()
    )
    
    # Получение настроек пользователя
    notifications = notification_manager.get_user_notifications(user_id)
    
    if not notifications:
        await update.message.reply_text(
            "⚠️ У вас нет настроенных уведомлений. Настройте режим обучения через меню '⚙️ Настройки обучения'.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Формирование тестового контекста
    class DummyJob:
        def __init__(self, data):
            self.data = data
            
    class DummyContext:
        def __init__(self, bot, data):
            self.bot = bot
            self.job = DummyJob(data)
    
    # Создание контекста с данными для отправки
    dummy_context = DummyContext(
        bot=context.bot,
        data={
            "user_id": user_id,
            "notification": notifications[0]
        }
    )
    
    # Вызов функции отправки уведомления
    try:
        await notification_manager._send_notification(dummy_context)
        
        await update.message.reply_text(
            f"✅ Тестовое уведомление успешно отправлено!\n\n"
            f"Настройки: {notifications[0]['events_count']} событий, {notifications[0]['figures_count']} деятелей\n\n"
            f"Проверьте, что уведомление содержит все необходимые материалы.",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка при отправке тестового уведомления: {e}\n\n"
            f"Попробуйте перенастроить уведомления через меню '⚙️ Настройки обучения'.",
            reply_markup=get_main_keyboard()
        )

# Функции для режима проверки знаний
async def start_testing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запуск режима проверки знаний"""
    keyboard = [
        [InlineKeyboardButton("По дате", callback_data="test_date")],
        [InlineKeyboardButton("По событию", callback_data="test_event")],
        [InlineKeyboardButton("По деятелю", callback_data="test_figure")],
        [InlineKeyboardButton("По достижению", callback_data="test_achievement")],
        [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        "📚 *Режим проверки знаний*\n\n"
        "Выберите тип тестирования:\n\n"
        "• *По дате* — вам показывается дата, нужно указать событие\n"
        "• *По событию* — вам показывается событие, нужно указать дату\n"
        "• *По деятелю* — вам показывается имя, нужно указать достижения\n"
        "• *По достижению* — вам показывается достижение, нужно указать имя\n\n"
        "💡 *Совет:* Регулярно проходите все типы тестов для комплексной подготовки."
    )
    
    if hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def handle_test_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка ответа на тест"""
    if context.user_data.get("state") == "testing":
        is_correct = await knowledge_test.check_answer(update, context, stats_manager)
        
        # Предложение продолжить тестирование
        keyboard = [
            [InlineKeyboardButton("Продолжить тестирование", callback_data="continue_testing")],
            [InlineKeyboardButton("Показать статистику", callback_data="statistics")],
            [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Выберите дальнейшее действие:",
            reply_markup=reply_markup
        )
        
        # Напоминаем о возможности отмены
        state_keyboard = get_state_keyboard(context.user_data["state"])
        await update.message.reply_text(
            "Или используйте кнопки быстрого доступа:",
            reply_markup=state_keyboard
        )

async def continue_testing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Продолжение тестирования"""
    # Получение текущего типа теста
    test_type = context.user_data.get("test_type")
    
    if test_type == "date":
        await knowledge_test.start_date_test(update, context)
    elif test_type == "event":
        await knowledge_test.start_event_test(update, context)
    elif test_type == "figure":
        await knowledge_test.start_figure_test(update, context)
    elif test_type == "achievement":
        await knowledge_test.start_achievement_test(update, context)
    else:
        # Если тип теста не определен, вернуться к выбору типа
        await start_testing(update, context)

# Функции для добавления данных
async def start_adding_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запуск режима добавления данных"""
    keyboard = [
        [InlineKeyboardButton("Добавить событие", callback_data="add_event")],
        [InlineKeyboardButton("Добавить деятеля", callback_data="add_figure")],
        [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        "➕ *Добавление данных*\n\n"
        "Вы можете расширить базу данных бота, добавляя свои материалы. "
        "Все добавленные данные будут использоваться в тестах и уведомлениях.\n\n"
        "Что вы хотите добавить?"
    )
    
    if hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def add_event_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало добавления события"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["state"] = "adding_event_date"
    
    await query.edit_message_text(
        "📅 *Добавление нового события*\n\n"
        "Введите дату события в одном из форматов:\n"
        "• Год: 1994\n"
        "• Период: 1941-1945\n"
        "• Точная дата: 27 июля 1990\n\n"
        "💡 *Совет:* Используйте формат, который наиболее точно соответствует характеру события.",
        parse_mode="Markdown"
    )
    
    # Отправляем отдельное сообщение с клавиатурой отмены
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text="Используйте кнопки ниже для управления:",
        reply_markup=get_state_keyboard(context.user_data["state"])
    )

async def handle_event_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка ввода даты события"""
    event_date = update.message.text
    
    # Сохранение даты
    context.user_data["temp_event_date"] = event_date
    context.user_data["state"] = "adding_event_description"
    
    # Запрос описания события
    await update.message.reply_text(
        f"✅ Дата *{event_date}* сохранена.\n\n"
        f"Теперь введите описание события:\n\n"
        f"💡 *Совет:* Описание должно быть информативным и содержать основные факты. "
        f"Например: 'Люблинская уния. Объединение ВКЛ и Польского королевства в Речь Посполитую'",
        parse_mode="Markdown",
        reply_markup=get_state_keyboard(context.user_data["state"])
    )

async def handle_event_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка ввода описания события"""
    event_description = update.message.text
    event_date = context.user_data["temp_event_date"]
    
    # Добавление события в базу данных
    try:
        event_id = data_manager.add_event(event_date, event_description)
        
        # Отправка подтверждения
        keyboard = [
            [InlineKeyboardButton("Добавить еще событие", callback_data="add_event")],
            [InlineKeyboardButton("Добавить деятеля", callback_data="add_figure")],
            [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ *Событие успешно добавлено!*\n\n"
            f"• *Дата:* {event_date}\n"
            f"• *Описание:* {event_description}\n\n"
            f"Событие будет использоваться в тестах и уведомлениях.",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
        # Возвращаем обычную клавиатуру
        main_keyboard = get_main_keyboard()
        await update.message.reply_text(
            "Используйте кнопки быстрого доступа:",
            reply_markup=main_keyboard
        )
        
        context.user_data["state"] = None
        
    except ValueError as e:
        # Обработка ошибок валидации
        await update.message.reply_text(
            f"⚠️ *Ошибка при добавлении события:* {str(e)}\n\n"
            f"Попробуйте еще раз.",
            parse_mode="Markdown",
            reply_markup=get_state_keyboard(context.user_data["state"])
        )

async def add_figure_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало добавления деятеля"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["state"] = "adding_figure_name"
    
    await query.edit_message_text(
        "👤 *Добавление нового исторического деятеля*\n\n"
        "Введите полное имя исторического деятеля:\n\n"
        "💡 *Совет:* Используйте официальное написание имени, как оно встречается в учебниках. "
        "Например: 'Франциск Скорина', 'Тадеуш Костюшко'",
        parse_mode="Markdown"
    )
    
    # Отправляем отдельное сообщение с клавиатурой отмены
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text="Используйте кнопки ниже для управления:",
        reply_markup=get_state_keyboard(context.user_data["state"])
    )

async def handle_figure_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка ввода имени деятеля"""
    figure_name = update.message.text
    
    # Сохранение имени
    context.user_data["temp_figure_name"] = figure_name
    context.user_data["state"] = "adding_figure_achievement"
    
    # Запрос достижения деятеля
    await update.message.reply_text(
        f"✅ Имя *{figure_name}* сохранено.\n\n"
        f"Теперь введите описание достижений или вклада этого деятеля:\n\n"
        f"💡 *Совет:* Укажите основной вклад в историю, годы жизни или деятельности. "
        f"Например: 'Белорусский первопечатник, переводчик Библии на старобелорусский язык'",
        parse_mode="Markdown",
        reply_markup=get_state_keyboard(context.user_data["state"])
    )

async def handle_figure_achievement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка ввода достижения деятеля"""
    figure_achievement = update.message.text
    figure_name = context.user_data["temp_figure_name"]
    
    # Добавление деятеля в базу данных
    try:
        figure_id = data_manager.add_figure(figure_name, figure_achievement)
        
        # Отправка подтверждения
        keyboard = [
            [InlineKeyboardButton("Добавить еще деятеля", callback_data="add_figure")],
            [InlineKeyboardButton("Добавить событие", callback_data="add_event")],
            [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ *Исторический деятель успешно добавлен!*\n\n"
            f"• *Имя:* {figure_name}\n"
            f"• *Достижение:* {figure_achievement}\n\n"
            f"Этот деятель будет использоваться в тестах и уведомлениях.",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
        # Возвращаем обычную клавиатуру
        main_keyboard = get_main_keyboard()
        await update.message.reply_text(
            "Используйте кнопки быстрого доступа:",
            reply_markup=main_keyboard
        )
        
        context.user_data["state"] = None
        
    except ValueError as e:
        # Обработка ошибок валидации
        await update.message.reply_text(
            f"⚠️ *Ошибка при добавлении деятеля:* {str(e)}\n\n"
            f"Попробуйте еще раз.",
            parse_mode="Markdown",
            reply_markup=get_state_keyboard(context.user_data["state"])
        )

# Функции для марафона
async def start_marathon_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало марафона по кнопке"""
    if hasattr(update, "callback_query") and update.callback_query:
        query = update.callback_query
        await query.answer()
        
        # Уведомление о начале марафона
        await query.edit_message_text(
            "🏆 *Марафон знаний*\n\n"
            "Приготовьтесь к серии из 5 разноплановых вопросов!\n\n"
            "• Отвечайте на каждый вопрос по очереди\n"
            "• Используйте ключевые термины в ответах\n"
            "• В конце вы получите свой результат и рекомендации\n\n"
            "Марафон начинается...",
            parse_mode="Markdown"
        )
    else:
        # Если вызов через сообщение, показываем подготовительное сообщение
        await update.message.reply_text(
            "🏆 *Марафон знаний*\n\n"
            "Приготовьтесь к серии из 5 разноплановых вопросов!\n\n"
            "• Отвечайте на каждый вопрос по очереди\n"
            "• Используйте ключевые термины в ответах\n"
            "• В конце вы получите свой результат и рекомендации\n\n"
            "Марафон начинается...",
            parse_mode="Markdown"
        )
    
    # Обновление состояния пользователя
    context.user_data["state"] = "marathon"
    
    # Показываем клавиатуру отмены
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text="Используйте эти кнопки во время марафона:",
        reply_markup=get_state_keyboard(context.user_data["state"])
    )
    
    # Запуск марафона с 5 вопросами
    await knowledge_test.start_marathon(update, context, 5)

async def next_marathon_question_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Переход к следующему вопросу марафона"""
    query = update.callback_query
    await query.answer()
    
    await knowledge_test.next_marathon_question(update, context)

# Функции для статистики
async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ статистики пользователя"""
    user_id = update.effective_user.id
    stats = stats_manager.get_user_stats(user_id)
    
    # Формирование сообщения со статистикой
    message, keyboard = format_statistics_message(stats, user_id)
    
    if hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.edit_message_text(
            message, 
            reply_markup=keyboard, 
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            message, 
            reply_markup=keyboard, 
            parse_mode="Markdown"
        )

def format_statistics_message(stats: dict, user_id: int):
    """Форматирует сообщение со статистикой"""
    # Формирование сообщения со статистикой
    message = "📊 *Ваша статистика обучения* 📊\n\n"
    
    if stats['tests_total'] == 0:
        message += "У вас пока нет статистики обучения.\n"
        message += "Начните проходить тесты и марафоны, чтобы отслеживать свой прогресс!\n\n"
        message += "💡 *Совет:* Регулярное тестирование - ключ к успешной подготовке."
    else:
        message += f"*Общая статистика:*\n"
        message += f"• Всего тестов: *{stats['tests_total']}*\n"
        message += f"• Правильных ответов: *{stats['tests_correct']}*\n"
        message += f"• Точность: *{stats['accuracy']}*%\n\n"
        
        if stats['test_types']:
            message += "*Результаты по категориям:*\n"
            for test_type, type_stats in stats['test_types'].items():
                type_accuracy = 0
                if type_stats['total'] > 0:
                    type_accuracy = round(type_stats['correct'] / type_stats['total'] * 100, 2)
                
                type_name = ""
                if test_type == "date":
                    type_name = "Даты"
                elif test_type == "event":
                    type_name = "События"
                elif test_type == "figure":
                    type_name = "Деятели"
                elif test_type == "achievement":
                    type_name = "Достижения"
                
                message += f"• *{type_name}*: {type_stats['correct']}/{type_stats['total']} ({type_accuracy}%)\n"
        
        # Добавление рекомендаций
        difficult_questions = stats_manager.get_difficult_questions(user_id, 3)
        recent_incorrect = stats_manager.get_recently_incorrect_questions(user_id, 3)
        
        if difficult_questions or recent_incorrect:
            message += "\n🔄 *Рекомендации для повторения:*\n"
            
            if difficult_questions:
                message += "*Сложные вопросы:*\n"
                for question in difficult_questions:
                    message += f"• {question['question']} (точность: {question['accuracy']}%)\n"
            
            if recent_incorrect:
                message += "\n*Недавние ошибки:*\n"
                for question in recent_incorrect:
                    message += f"• {question['question']}\n"
            
            message += "\n💡 *Совет:* Сосредоточьтесь на темах с наибольшим количеством ошибок."
    
    # Добавление кнопок для дальнейших действий
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Начать тестирование", callback_data="testing")],
        [InlineKeyboardButton("Пройти марафон", callback_data="start_marathon")],
        [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
    ])
    
    return message, keyboard

async def check_jobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверка запланированных задач уведомлений"""
    jobs = context.job_queue.get_jobs_by_name("notification")
    
    if not jobs:
        await update.message.reply_text(
            "⚠️ Нет запланированных уведомлений. Настройте режим обучения через меню '⚙️ Настройки обучения'.",
            reply_markup=get_main_keyboard()
        )
        return
    
    now = datetime.datetime.now()
    
    message = f"📋 *Запланированные уведомления ({len(jobs)} шт.):*\n\n"
    
    for i, job in enumerate(jobs, 1):
        # Получаем информацию о задаче
        next_run = job.next_t
        notification = job.data.get("notification", {})
        time_str = notification.get("time", "неизвестно")
        
        # Расчет времени до следующего запуска
        time_diff = next_run - now if next_run > now else now - next_run
        time_diff_str = f"{time_diff.seconds // 3600} ч. {(time_diff.seconds % 3600) // 60} мин."
        
        message += f"{i}. Уведомление на {time_str}:\n"
        message += f"   • Следующая отправка: {next_run.strftime('%d.%m.%Y %H:%M')}\n"
        message += f"   • {('Через: ' + time_diff_str) if next_run > now else ('Просрочено на: ' + time_diff_str)}\n"
        message += f"   • Контент: {notification.get('events_count', 0)} событий, {notification.get('figures_count', 0)} деятелей\n\n"
    
    message += "💡 *Совет:* Если уведомления не приходят, проверьте настройки часового пояса и перезапустите бота."
    
    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# Обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка сообщений в зависимости от текущего состояния"""
    state = context.user_data.get("state")
    message_text = update.message.text
    
    # Обработка запроса на показ справки
    if message_text == "❓ Справка":
        await show_context_help(update, context)
        return
    
    if message_text == "❌ Отменить действие":
        await cancel_command(update, context)
        return
    
    # Обработка команд быстрого доступа через Reply Keyboard
    if not state:
        if message_text == "📚 Проверка знаний":
            await start_testing(update, context)
            return
        
        elif message_text == "🏆 Марафон":
            await start_marathon_callback(update, context)
            return
        
        elif message_text == "📊 Статистика":
            await show_statistics(update, context)
            return
        
        elif message_text == "➕ Добавить данные":
            await start_adding_data(update, context)
            return
        
        elif message_text == "⚙️ Настройки обучения":
            await start_learning(update, context)
            return
    
    # Обработка состояний
    if state == "setting_notifications_count":
        await handle_notification_count(update, context)
    
    elif state == "setting_notification_time":
        await handle_notification_time(update, context)
    
    elif state == "setting_events_count":
        await handle_events_count(update, context)
    
    elif state == "setting_figures_count":
        await handle_figures_count(update, context)
    
    elif state == "testing":
        await handle_test_answer(update, context)
    
    elif state == "marathon":
        await knowledge_test.check_marathon_answer(update, context, stats_manager)
    
    elif state == "adding_event_date":
        await handle_event_date(update, context)
    
    elif state == "adding_event_description":
        await handle_event_description(update, context)
    
    elif state == "adding_figure_name":
        await handle_figure_name(update, context)
    
    elif state == "adding_figure_achievement":
        await handle_figure_achievement(update, context)
    
    else:
        # Если состояние не определено и сообщение не обработано выше
        main_keyboard = get_main_keyboard()
        
        keyboard = [
            [InlineKeyboardButton("Справка", callback_data="help_main")],
            [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
        ]
        inline_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Я не понимаю эту команду. Воспользуйтесь кнопками для навигации:",
            reply_markup=inline_markup
        )
        
        # Напоминаем о кнопках быстрого доступа
        await update.message.reply_text(
            "Или используйте эти кнопки для быстрого доступа:",
            reply_markup=main_keyboard
        )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /cancel для отмены текущего действия"""
    # Получаем текущее состояние пользователя
    state = context.user_data.get("state")
    
    if not state or state == "main_menu":
        await update.message.reply_text(
            "Нет активных действий для отмены.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Сбрасываем состояние
    old_state = context.user_data["state"]
    context.user_data["state"] = None
    
    # Отправляем уведомление об отмене
    await update.message.reply_text(
        f"❌ Действие отменено.",
        reply_markup=get_main_keyboard()
    )
    
    # Возвращаемся в главное меню
    keyboard = [
        [InlineKeyboardButton("Вернуться в главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Выберите дальнейшее действие:",
        reply_markup=reply_markup
    )

def main() -> None:
    """Запуск бота с обработкой ошибок соединения"""
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Ошибка: Не найден токен бота. Проверьте переменную TELEGRAM_BOT_TOKEN")
        return

    # Создаем отдельный объект для таймаутов запросов
    # Вместо передачи словаря используем правильный метод
    from telegram.request import HTTPXRequest
    request = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=30.0,
        write_timeout=30.0,
        connect_timeout=30.0,
        pool_timeout=30.0,
    )
    
    print("🚀 Запуск бота для подготовки к экзамену по истории Беларуси...")
    
    try:
        # Создание приложения с настроенными таймаутами
        application = Application.builder().token(token).request(request).build()
        
        # Добавление обработчиков
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("cancel", cancel_command))
        application.add_handler(CommandHandler("test_notification", test_notification_command))
        application.add_handler(CommandHandler("check_jobs", check_jobs_command))
        
        # Обработчик для callback-запросов справки
        application.add_handler(CallbackQueryHandler(help_callback, pattern="^help_"))
        
        # Общий обработчик callback-запросов
        application.add_handler(CallbackQueryHandler(button_callback))
        
        # Обработчик текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Добавление глобального обработчика ошибок
        application.add_error_handler(error_handler)
        
        # Настройка автоматического старта уведомлений при запуске бота
        async def post_init(application: Application) -> None:
            try:
                await notification_manager.schedule_notifications(application)
                print("✅ Уведомления настроены и запущены!")
            except Exception as e:
                print(f"⚠️ Предупреждение: Ошибка при настройке уведомлений: {e}")
                logger.error(f"Ошибка при настройке уведомлений: {e}", exc_info=True)
        
        # Регистрация post_init функции
        application.post_init = post_init
        
        # Запуск бота с расширенными настройками
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            timeout=30,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=30,
        )
        
    except error.NetworkError as e:
        print(f"❌ Ошибка сети при подключении к Telegram API: {e}")
        print("\nВозможные причины проблемы:")
        print("1. Проблемы с подключением к интернету")
        print("2. Блокировка API Telegram в вашей сети")
        print("3. Временные проблемы на стороне серверов Telegram")
        print("\nРекомендации:")
        print("- Проверьте подключение к интернету")
        print("- Попробуйте использовать VPN если API заблокирован")
        print("- Попробуйте запустить бота позже")
    
    except error.TimedOut as e:
        print(f"❌ Превышено время ожидания при подключении к Telegram API: {e}")
        print("\nРекомендации:")
        print("- Проверьте скорость вашего интернет-соединения")
        print("- Увеличьте значения таймаутов в настройках")
        print("- Попробуйте запустить бота позже")
    
    except error.Unauthorized as e:
        print(f"❌ Ошибка авторизации: {e}")
        print("\nВероятная причина: неверный токен бота")
        print("\nРекомендации:")
        print("- Проверьте правильность токена в файле .env")
        print("- Убедитесь, что токен не содержит лишних символов")
        print("- Получите новый токен у @BotFather в Telegram если необходимо")
    
    except Exception as e:
        print(f"❌ Непредвиденная ошибка при запуске бота: {e}")
        logger.error(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
        print("\nПопробуйте следующие действия:")
        print("1. Проверьте журналы ошибок для получения дополнительной информации")
        print("2. Обновите библиотеку python-telegram-bot: pip install python-telegram-bot --upgrade")
        print("3. Перезапустите компьютер и попробуйте снова")

# Обработчик ошибок для всего приложения
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок для логирования и восстановления после сбоев"""
    # Получение информации об ошибке
    error = context.error
    
    # Логирование ошибки
    logger.error(f"Произошла ошибка при обработке запроса: {error}", exc_info=context.error)
    
    # Попытка уведомить пользователя об ошибке, если update доступен
    if isinstance(update, Update) and update.effective_chat:
        error_message = "⚠️ Произошла ошибка при обработке вашего запроса."
        
        if isinstance(error, error.TimedOut):
            error_message = "⚠️ Превышено время ожидания ответа. Пожалуйста, повторите запрос."
        elif isinstance(error, error.NetworkError):
            error_message = "⚠️ Проблема с сетевым соединением. Пожалуйста, повторите запрос позже."
        elif isinstance(error, error.BadRequest):
            error_message = "⚠️ Неверный запрос. Пожалуйста, попробуйте другую команду."
        
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{error_message}\n\nМожете продолжить работу с ботом.",
                reply_markup=get_main_keyboard()
            )
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}")
            
if __name__ == "__main__":
    main()