import aiogram
import asyncio
import random
import os

from settings.config import bot_token, channel_ids, channel_links

from time import sleep
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    CallbackQuery
)

form_router = Router()

class user_fsm(StatesGroup):
    code = State()
    action_type = State()

def file_init():
    files_list = ['Фильмы.txt', 'Сериалы.txt']
    for file in files_list:
        if not os.path.exists(file):
            print(f'Файл: {file} не существует! Создаю новый')
            with open(file, 'w', encoding='utf-8'):
                pass
    
    with open('Фильмы.txt', 'r', encoding='utf-8') as file:
        details = [line.strip().split(':') for line in file.readlines()]
        films_dict = {code: title for code, title in details}
    
    with open('Сериалы.txt', 'r', encoding='utf-8') as file:
        details = [line.strip().split(':') for line in file.readlines()]
        serials_dict = {code: title for code, title in details}
    
    return films_dict, serials_dict

films_dict, serials_dict = file_init()

@form_router.message(lambda message: message.text == 'Случайный фильм🎬' or message.text == 'Случайный сериал🎬')
async def search_random(message: Message):
    if message.text == 'Случайный фильм🎬':
        code = random.choice(list(films_dict.keys()))
        film = films_dict.get(code)
        await message.answer(f'✅ Случайный фильм найден!\n🎬 Название фильма: {film}\n🔎 Код фильма: {code}')
    elif message.text == 'Случайный сериал🎬':
        code = random.choice(list(films_dict.keys()))
        serial = serials_dict.get(code)
        await message.answer(f'✅ Случайный сериал найден!\n🎬 Название сериала: {serial}\n🔎 Код фильма: {code}')

@form_router.message(lambda message: message.text == 'Найти фильм по коду🔎' or message.text == 'Найти сериал по коду🔎')
async def get_code(message: Message, state: FSMContext):
    await message.answer('⚙️ Введи код: ')
    if message.text == 'Найти фильм по коду🔎':
        action_type = 'Film'
    elif message.text == 'Найти сериал по коду🔎':
        action_type = 'Serial'
    await state.update_data(action_type=action_type)
    await state.set_state(user_fsm.code)

@form_router.message(user_fsm.code)
async def search_code(message: Message, state: FSMContext):
    data = await state.get_data()
    action_type = data.get('action_type')

    if action_type == 'Film':
        film = films_dict.get(message.text)
        if film: 
            await message.answer(f'✅ Фильм найден!\n🎬 Название: {film}\n🔎 Код: {message.text}') 
        else:
            await message.answer('❌ Фильм не найден')
    elif action_type == 'Serial':
        serial = serials_dict.get(message.text)
        if serial: 
            await message.answer(f'✅ Сериал найден!\n🎬 Название: {serial}\n🔎 Код: {message.text}') 
        else:
            await message.answer('❌ Сериал не найден')

async def bot_main(message: Message, bot):
    keyboard = ReplyKeyboardMarkup(keyboard=(
        [KeyboardButton(text='Найти фильм по коду🔎')],
        [KeyboardButton(text='Найти сериал по коду🔎')],
        [KeyboardButton(text='Случайный фильм🎬')],
        [KeyboardButton(text='Случайный сериал🎬')],
    ), resize_keyboard=True)

    await bot.send_message(chat_id=message.chat.id, text='⚙️ Выберите действие: ', reply_markup=keyboard)

@form_router.callback_query(lambda c: c.data == 'Check Subscription')
async def check_subscription(callback_query: CallbackQuery, bot):
    user_id = callback_query.from_user.id
    user_subscriptions = {chat_id: False for chat_id in channel_ids}

    processing_message = await bot.send_message(chat_id=user_id, text='⏳ Проверяю статус подписок...')
    for chat_id in channel_ids:
        try:
            user_result = await bot.get_chat_member(chat_id, user_id)
            if user_result.status in ['administrator', 'creator', 'member']:
                user_subscriptions[chat_id] = True
            else:
                await bot.edit_message_text(chat_id=user_id, message_id=processing_message.message_id, text='❌ Ты не подписан на каналы!')
        except Exception as e:
            print(f'Возникла ошибка: {e}')
            await bot.edit_message_text(chat_id=user_id, message_id=processing_message.message_id, text='❌ Возникла ошибка, при проверке твоего статуса подписки. Повтори попытку позже!')
    if all(user_subscriptions.values()):
        await bot.edit_message_text(chat_id=user_id, message_id=processing_message.message_id, text='✅ Спасибо за подписку, теперь ты можешь продолжить использовать бота!')
        sleep(2)
        await bot.delete_message(chat_id=user_id, message_id=processing_message.message_id)
        await bot_main(callback_query.message, bot)

@form_router.message(CommandStart())
async def bot_start(message: Message, bot):
    await message.answer('👋 Привет! Я бот который выдаст тебе название \n🎥 фильмов/сериалов по коду.')

    channel_info_list = [await bot.get_chat(link) for link in channel_links]
    channel_title_list = [channel_info.title for channel_info in channel_info_list]

    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text=channel_title, url=f'https://t.me/{link.replace("@", "")}')
            for link, channel_title in zip(channel_links, channel_title_list)
        ],
        [
            types.InlineKeyboardButton(text='☑️ Проверить подписки', callback_data='Check Subscription')
        ]
    ])
    
    await message.answer('🛑 Для продолжения работы, тебе необходимо подписаться на эти телеграм каналы!', reply_markup=markup)

async def bot_init():
    bot = Bot(token=bot_token)
    dp = Dispatcher()
    dp.include_router(form_router)
    await dp.start_polling(bot)

print('Бот запущен!\nДля выхода: CTRL+C')

if __name__ == '__main__':
    asyncio.run(bot_init())