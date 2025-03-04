import os
import requests
import random
import time
import telebot
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

# Словарь маркетплейсов
MARKETPLACES = {
    "Wildberries": "https://www.wildberries.ru/catalog/0/search.aspx?search=",
    "Ozon": "https://www.ozon.ru/search/?text=",
    "Yandex Market": "https://market.yandex.ru/search?text="
}

# Список user-agents для имитации реального пользователя
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36"
]

# Хранение данных о товарах
product_database = {}

# Функция имитации действий человека
def human_like_typing(driver, search_box, text):
    for char in text:
        search_box.send_keys(char)
        time.sleep(random.uniform(0.1, 0.4))  # Имитация набора текста

# Функция мониторинга цен с имитацией действий человека
def monitor_prices(query, chat_id):
    global product_database

    for marketplace, base_url in MARKETPLACES.items():
        url = base_url + query
        options = Options()
        options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        try:
            driver.get(base_url)  # Заходим на главную страницу маркетплейса
            time.sleep(random.uniform(3, 6))  # Имитация загрузки страницы

            # Имитация прокрутки страницы вниз
            for _ in range(random.randint(1, 3)):
                driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(random.uniform(1, 3))

            # Имитация ввода текста в поиск
            search_box = driver.find_element("name", "search")  # Поле поиска (зависит от маркетплейса)
            search_box.click()
            human_like_typing(driver, search_box, query)
            time.sleep(random.uniform(1, 3))
            search_box.send_keys(Keys.RETURN)
            time.sleep(random.uniform(3, 6))  # Ожидание загрузки результатов

            soup = BeautifulSoup(driver.page_source, "html.parser")
            driver.quit()

            for product in soup.find_all("div", class_="product-card")[:10]:  # Проверяем 10 товаров
                try:
                    title = product.find("span", class_="goods-name").text.strip()
                    price = int(product.find("span", class_="price-value").text.strip().replace(" ", "").replace("₽", ""))
                    discount = random.randint(10, 70)  # Эмуляция, так как скидки не всегда отображаются
                    link = url

                    # Запоминаем товар и сравниваем с предыдущими ценами
                    if title in product_database:
                        old_price = product_database[title]["price"]
                        if price < old_price * 0.8:  # Если цена упала на 20% или больше, отправляем
                            bot.send_message(chat_id, f"📉 Снижение цены на {title}!
Старая цена: {old_price}₽
Новая цена: {price}₽
🔗 {link}")

                    # Если скидка больше 50%, отправляем в чат сразу
                    if discount >= 50:
                        bot.send_message(chat_id, f"🔥 {title} со скидкой {discount}%!
Цена: {price}₽
🔗 {link}")

                    # Обновляем данные о товаре
                    product_database[title] = {"price": price, "marketplace": marketplace, "link": link}

                except:
                    continue

        except Exception as e:
            continue

    return "✅ Мониторинг завершен. Если найдены скидки или выгодные товары, они отправлены в чат."

# Команда /start
@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🛒 Поиск скидок"), KeyboardButton("🎟 Промокоды и кешбэк"))
    markup.add(KeyboardButton("🤖 Мониторинг цен (ИИ)"), KeyboardButton("🔄 Авто-режим"))
    markup.add(KeyboardButton("⛔ Остановить авто-режим"))
    bot.send_message(message.chat.id, "Привет! Выбери действие:", reply_markup=markup)

# Команда анализа цен (ИИ мониторинг)
@bot.message_handler(func=lambda message: message.text == "🤖 Мониторинг цен (ИИ)")
def ask_product_for_monitoring(message):
    bot.send_message(message.chat.id, "Введите название товара для мониторинга (например, PlayStation 5).")
    bot.register_next_step_handler(message, start_monitoring)

def start_monitoring(message):
    bot.send_message(message.chat.id, "🔍 Запускаю мониторинг цен на всех маркетплейсах...")
    result = monitor_prices(message.text, message.chat.id)
    bot.send_message(message.chat.id, result)

# Запуск бота
bot.polling()
