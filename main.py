import telebot
import requests
import time
import sys
import os
import random
import string
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

# --- 1. КОНФИГУРАЦИЯ ---
# Получение настроек из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")
GREEN_API_BASE_URL_SEND = os.getenv("GREEN_API_BASE_URL_SEND")
GREEN_API_BASE_URL_FILE = os.getenv("GREEN_API_BASE_URL_FILE")

# Проверка наличия обязательных переменных
if not all([BOT_TOKEN, TARGET_CHAT_ID, GREEN_API_BASE_URL_SEND, GREEN_API_BASE_URL_FILE]):
    print("!!! ОШИБКА КОНФИГУРАЦИИ: Проверьте, заполнены ли BOT_TOKEN, TARGET_CHAT_ID и GREEN_API_BASE_URL в файле .env")
    sys.exit(1)

# Формирование полных URL Green-API
GREEN_API_SEND_MESSAGE_URL = f"{GREEN_API_BASE_URL_SEND}"
GREEN_API_SEND_FILE_UPLOAD_URL = f"{GREEN_API_BASE_URL_FILE}"

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# --- 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def generate_random_filename(extension):
    """Генерирует уникальное имя файла с случайным суффиксом."""
    random_suffix = ''.join(random.choices(string.digits, k=4))
    return f"temp_{random_suffix}.{extension}"

def get_mime_type(extension):
    """Возвращает MIME-тип по расширению. Добавлена поддержка общих типов."""
    mime_type_map = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'zip': 'application/zip',
        'rar': 'application/x-rar-compressed',
        'default': 'application/octet-stream' 
    }
    return mime_type_map.get(extension.lower(), mime_type_map['default'])

# --- 3. ФУНКЦИЯ ОТПРАВКИ ТЕКСТА ---

def sendMaxMessage(text):
    """Отправляет полученный текст через Green-API (для обычных постов)."""
    text_to_send = str(text) 
    
    payload = {
        "chatId": TARGET_CHAT_ID, 
        "message": text_to_send,
        "customPreview": {
            "title": "Новое текстовое сообщение из Telegram-канала" 
        }
    }
    
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(GREEN_API_SEND_MESSAGE_URL, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            print(f"[{time.strftime('%H:%M:%S')}] ✅ Текст успешно отправлен через Green-API.")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ Ошибка при отправке текста. Статус: {response.status_code}")
            print(f"Тело ответа: {response.text.encode('utf8')}")
            
    except requests.exceptions.RequestException as e:
        print(f"[{time.strftime('%H:%M:%S')}] 🛑 Ошибка сетевого запроса к Green-API (текст): {e}")

# --- 4. ФУНКЦИЯ ОТПРАВКИ ФАЙЛОВ ---

def sendMaxFile(caption, file_path, file_name):
    """
    Отправляет любой файл через Green-API методом sendFileByUpload.
    """
    print(f"[{time.strftime('%H:%M:%S')}] Запуск процесса отправки файла: {file_name}")
    
    file_extension = file_name.split('.')[-1] if '.' in file_name else 'bin'
    mime_type = get_mime_type(file_extension)
    
    # Параметры, передаваемые в секции 'data'
    payload = {
        'chatId': TARGET_CHAT_ID, 
        'caption': caption or '', 
        'fileName': file_name 
    }
    
    try:
        with open(file_path, 'rb') as f:
            files = [
                ('file', (file_name, f, mime_type)) 
            ]
            
            response = requests.post(
                GREEN_API_SEND_FILE_UPLOAD_URL, 
                data=payload, 
                files=files, 
                timeout=60
            )
            
            if response.status_code == 200:
                print(f"[{time.strftime('%H:%M:%S')}] ✅ Файл '{file_name}' успешно отправлен через Green-API.")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] ❌ Ошибка при отправке файла. Статус: {response.status_code}")
                print(f"Тело ответа: {response.text.encode('utf8')}")
                
    except FileNotFoundError:
        print(f"[{time.strftime('%H:%M:%S')}] 🛑 Ошибка: Временный файл не найден: {file_path}")
    except requests.exceptions.RequestException as e:
        print(f"[{time.strftime('%H:%M:%S')}] 🛑 Ошибка сетевого запроса к Green-API (Upload): {e}")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] 🛑 Неизвестная ошибка при отправке файла: {e}")


# --- 5. ЛОГИКА БОТА ---

@bot.channel_post_handler(content_types=['text', 'photo', 'document'])
def handle_channel_post(message):
    
    content_type = message.content_type
    
    # 1. ТЕКСТОВЫЕ СООБЩЕНИЯ
    if content_type == 'text':
        print(f"[{time.strftime('%H:%M:%S')}] 📜 Получено новое ТЕКСТОВОЕ сообщение.")
        text = message.text or ""
        sendMaxMessage(text)
        return

    # 2. ФАЙЛОВЫЕ СООБЩЕНИЯ (ФОТО И ДОКУМЕНТЫ)
    
    file_id = None
    original_filename = None
    caption = message.caption or ""
    
    if content_type == 'photo':
        print(f"[{time.strftime('%H:%M:%S')}] 🖼️ Получено новое ИЗОБРАЖЕНИЕ.")
        file_id = message.photo[-1].file_id
        original_filename = generate_random_filename('jpg') 
    
    elif content_type == 'document':
        print(f"[{time.strftime('%H:%M:%S')}] 📁 Получен новый ДОКУМЕНТ.")
        file_id = message.document.file_id
        original_filename = message.document.file_name or generate_random_filename('dat')
    
    else:
        return 

    # --- Общая логика скачивания и отправки файла ---
    
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    # Генерируем временное имя файла для локального сохранения
    file_extension_temp = original_filename.split('.')[-1]
    temp_filename = generate_random_filename(file_extension_temp)
    
    try:
        with open(temp_filename, 'wb') as new_file:
            new_file.write(downloaded_file)
        print(f"[{time.strftime('%H:%M:%S')}] Временный файл сохранен как: {temp_filename}")
        
        # 4. Вызываем общую функцию отправки файла
        sendMaxFile(caption, temp_filename, original_filename)
        
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%M')}] Ошибка при сохранении/отправке файла: {e}")
    finally:
        # 5. Обязательно удаляем временный файл
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
            print(f"[{time.strftime('%H:%M:%S')}] Временный файл {temp_filename} удален.")


# --- 6. ЗАПУСК ПОСТОЯННОГО ОПРОСА ---

if __name__ == '__main__':
    print("-----------------------------------------------------")
    print("Бот запущен. Ожидает НОВЫХ сообщений в канале...")
    print("Для остановки нажмите Ctrl+C.")
    print("-----------------------------------------------------")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=60)
            
        except requests.exceptions.ReadTimeout:
            print(f"[{time.strftime('%H:%M:%S')}] Таймаут, продолжаем опрос.")
            time.sleep(1) 
        except Exception as e:
            print(f"\n!!! КРИТИЧЕСКАЯ ОШИБКА, ПЕРЕЗАПУСК ЧЕРЕЗ 10 СЕКУНД: {e}")
            time.sleep(10)
        except KeyboardInterrupt:
            print("\nПрограмма остановлена пользователем.")

            sys.exit(0)
