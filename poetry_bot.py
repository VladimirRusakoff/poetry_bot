import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.filters import Command
#
import asyncio
#
from dotenv import load_dotenv
#
from httpx import AsyncClient
#
from sql_lite import init_db
from sql_lite import add_new_action

load_dotenv()

bot = Bot(token=os.getenv('TELEGRAM_TOKEN'), timeout=60)
dp = Dispatcher()

# функция для генерации стихотворений и хокку через perplexity
async def generate_poem_perplexity(theme: str, poem_type: str) -> str:
    try:
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            return "Error: Don't have API key"
        
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # настраиваем контент и промт в зависимости от типа 
        if poem_type == "Стихотворение":
            content = (
                "Ты - талантливый поэт, мастер русской поэзии. "
                "Ты умеешь создавать красивые, глубокие и эмоциональные стихотворения, "
                "соблюдая все правила стихосложения, включая рифму, ритм и метр. "
                "Твой стиль сочетает классические традиции с современной образностью."
            )
            prompt = (
                f"Напиши красивое и оригинальное стихотворение на тему '{theme}' на русском языке. "
                "Стихотворение должно:\n"
                "- Состоять из 4-8 строк (1-2 строфы)\n"
                "- Иметь четкую рифму и ритм\n"
                "- Содержать яркие метафоры или образы\n"
                "- Передавать глубокую эмоцию или мысль\n"
                "- Быть понятным и выразительным\n"
                "- Избегать банальностей и клише\n"
                "- Иметь законченную мысль\n"
                "- Использовать богатство русского языка\n\n"
                "Стихотворение должно быть кратким, но ёмким, каждое слово должно нести смысловую нагрузку."
            )
            temp = 0.75;
        elif poem_type == "Хокку":
            content = (
                "Ты - мастер японской поэзии, специализирующийся на написании хокку. "
                "Ты глубоко понимаешь философию и эстетику жанра хокку, включая принципы "
                "сезонности (киго), момента (кирэдзи) и созерцательности."
            )
            prompt = (
                f"Создай хокку на тему '{theme}' на русском языке. Хокку должно:\n"
                "- Строго соблюдать структуру 5-7-5 слогов\n"
                "- Содержать яркий образ или метафору\n"
                "- Включать элемент природы или времени года\n"
                "- Передавать мимолётное впечатление или состояние\n"
                "- Быть философским и созерцательным\n"
                "- Использовать простые, но выразительные слова\n"
                "- Создавать чёткую визуальную картину\n\n"
                "После хокку укажи количество слогов в скобках для каждой строки."
            )
            temp = 0.7
        elif poem_type == "Анекдот":
            content = "Ты - профессиональный комик с отличным чувством юмора. Ты умеешь рассказывать короткие, смешные и интересные анекдоты."
            prompt = (
                 f"Расскажи короткий и смешной анекдот на тему '{theme}'. "
                "Анекдот должен быть:\n"
                "- Оригинальным и неизбитым\n"
                "- Без грубости и пошлости\n"
                "- С неожиданной концовкой\n"
                "- Понятным широкой аудитории\n"
                "- Длиной не более 5-6 предложений\n"
                "- На русском языке\n"
                "Если тема сложная, можно сделать анекдот с лёгкой иронией или добрым юмором."
            )
            temp = 0.8
        else: # тост
            content = "Ты - талантливый оратор и мастер тостов, который умеет создавать яркие, душевные и запоминающиеся речи."
            prompt = (
                f"Сочини короткий, оригинальный и душевный тост на тему '{theme}' на русском языке. "
                "Тост должен быть позитивным, запоминающимся и с элементами юмора. "
                "Длина: 2-3 предложения. "
                "Начни со слов 'Я предлагаю поднять бокалы...' или 'Давайте выпьем за...'. "
                "Заверши тост ярким пожеланием."
            )
            temp = 0.8


        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": content
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 300,  # добавляем ограничение на длину ответа
            "temperature": temp,  # добавляем параметр температуры
            "stream": False
        }

        async with AsyncClient(timeout=30.0) as client:
            for attempt in range(3): # добавляем повторные попытки
                try:
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()

                    result = response.json()
                    if 'choices' in result and result['choices']:
                        content = result['choices'][0]['message']['content']
                        if content: 
                            return content.strip()
                        
                    raise ValueError("Uncorrect response from API")
                    
                except Exception as e:
                    print(f"Попытка {attempt + 1} не удалась: {str(e)}")
                    if attempt == 2: # последняя попытка
                        return f"Произошла ошибка при генерации. Пожалуйста, попробуйте повторить запрос позже. ({str(e)})"
                    await asyncio.sleep(1)

    except Exception as e:
        return f"Ошибка при генерации стихотворения: {str(e)}"
    

# создание кнопок
def get_keyboard():
    # список кнопок
    buttons = [
        [KeyboardButton(text="Стихотворение")],
        [KeyboardButton(text="Хокку")],
        [KeyboardButton(text="Тост")],
        [KeyboardButton(text="Анекдот")]
    ]
    #
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    #
    return keyboard

# словарь для хранения тем пользователей
user_themes = {}

# обработчик команды /start
@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    await message.reply(
            "Привет! Я помогу сгенерировать стихотворение, хокку, анекдот или тост. \n"
            "Напишите тему, а затем выберите тип произведения с помощью кнопок.",
            reply_markup=get_keyboard()
        )
    
# обработчик текстовых сообщений
@dp.message(F.text & ~F.text.in_(["Хокку", "Стихотворение", "Тост", "Анекдот"]))
async def handle_theme(message: types.Message):
    user_themes[message.from_user.id] = message.text
    await message.reply(
        f"Тема: '{message.text}'\n"
        "Теперь выберите тип произведения с помощью кнопок ниже:",
        reply_markup=get_keyboard()
    )

# обработчик нажатия на кнопки "Хокку", "Стихотворение", "Тост", "Анекдот"
@dp.message(F.text & F.text.in_(["Хокку", "Стихотворение", "Тост", "Анекдот"]))
async def hokku_click(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_themes:
        await message.reply(f"Пожалуйста, сначала напишите тему для {message.text}")
        return 
    
    theme = user_themes[user_id]
    poem = await generate_poem_perplexity(theme, message.text)
    del user_themes[user_id] # очищаем сохраненную тему
    # добавленяем в БД
    add_new_action(message.from_user.id, message.from_user.username, 
                    message.from_user.first_name, message.from_user.last_name,
                    message.text, theme, poem)
    #
    await message.reply(poem)

# вызов функции main
async def main():
    try:
        init_db() # инициализируем БД при запуске
        while True:
            try:
                await dp.start_polling(bot)
            except Exception as e:
                print(f"Ошибка при работе бота: {e}")
                await asyncio.sleep(5) # пауза перед повторным подключением
    except KeyboardInterrupt:
        print("Бот остановлен")

if __name__ == '__main__':
    asyncio.run(main())