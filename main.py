import asyncio
import random

from func.global_var import game_states, set_game_state, set_count_state, user_count_date
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest
from aiogram.types import Message
from aiogram.filters import Command

from aiogram.enums.parse_mode import ParseMode

from misc import bot, dp




horses = ['🐎', '🐴', '🏇']
bets = {}
track_length = 20  # Длина трассы



@dp.message(Command("horse_help"))
async def start(message: Message):
    await message.answer('Добро пожаловать на скачки! Используйте /race для начала гонки.')


async def countdown(message: Message, start: int = 5):
    for i in range(start, 0, -1):
        await message.edit_text(f"Гонка начнётся через {i} секунд...")
        await asyncio.sleep(1)
    await message.edit_text("Гонка началась!")


async def check_game(msg):
    chat_id = str(msg.chat.id)
    if game_states.get(chat_id) is True:
        await msg.answer(text="Гонка уже запущена")
    else:
        await race(msg)

@dp.message(Command("race"))
async def start_race(msg: Message):
    await check_game(msg)


# Команда для сбора ставок
@dp.message(Command("pay"))
async def pay_bet(message: Message):

    try:
        # Разбиваем сообщение на части
        _, amount, number = message.text.split()
        amount = int(amount)
        number = int(number)

        if amount <= 0 or number <= 0:
            await message.reply("Сумма и число должны быть положительными!")
            return

        user_id = message.from_user.id
        chat_id = message.chat.id
        username = str(message.from_user.first_name)

        # Инициализируем словарь для чата, если его еще нет
        if chat_id not in bets:
            bets[chat_id] = {}

        # Записываем ставку
        bets[chat_id][user_id] = {
            'user_id': user_id,
            'username': username,
            'amount': amount,
            'number': number
        }

        await message.reply(f"{username} сделал ставку: сумма {amount}, лошадь: {number}")

    except ValueError:
        await message.reply("Используйте формат: /pay сумма число")


async def race(message: Message):
    chat_id = message.chat.id
    if chat_id not in bets or not bets[chat_id] or game_states.get(chat_id) is True:
        await message.answer("Ставок нет!")
        return
    set_game_state(message, state=True)
    race_message = await message.answer("Подготовка к гонке...")
    await countdown(race_message)  # Обратный отсчёт перед началом гонки

    positions = [track_length - 1, track_length - 1, track_length - 1]  # Начальные позиции лошадей
    await race_message.edit_text('Скачки начались!\n' + render_race(positions), parse_mode=ParseMode.MARKDOWN)

    while min(positions) > 0:
        await asyncio.sleep(2)  # Пауза между обновлениями, увеличена до 2 секунд для уменьшения нагрузки
        new_positions = [pos - random.randint(0, 2) for pos in positions]
        if new_positions != positions:
            positions = new_positions
            try:
                await race_message.edit_text('Скачки продолжаются!\n' + render_race(positions),
                                             parse_mode=ParseMode.MARKDOWN)
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
            except TelegramBadRequest:
                pass

    winner_number = positions.index(min(positions)) + 1

    await announce_winner(race_message, winner_number)





async def announce_winner(race_message: Message, winner_number: int):
    chat_id = race_message.chat.id
    await race_message.delete()
    # Находим всех победителей

    winners = [bet for bet in bets[chat_id].values() if bet['number'] == winner_number]

    # Формируем сообщение с результатами
    results = f"Победила лошадь под номером: {winner_number}\n\nРезультаты:\n"
    total_pot = sum(bet['amount'] for bet in bets[chat_id].values())

    if winners:
        # Разделить выигрыш между победителями
        split_amount = total_pot // len(winners)
        for winner in winners:
            results += f"{winner['username']} выиграл {split_amount}!\n"
            print(user_count_date.get(winner['user_id']))
            if user_count_date.get(winner['user_id']) is None:
                set_count_state(user_id=winner['user_id'], state=split_amount)
            else:
                old_count = user_count_date.get(winner['user_id'])
                new_count = split_amount + old_count
                set_count_state(user_id=winner['user_id'], state=new_count)
    else:
        results += "Нет победителей!\n"

    # Отправляем сообщение с результатами
    await race_message.answer(text=results, parse_mode=ParseMode.MARKDOWN)
    # Очищаем хранилище ставок только для текущего чата
    bets[chat_id].clear()
    set_game_state(race_message, state=False)


def render_race(positions):
    track = [[' ' for _ in range(track_length)] for _ in range(len(horses))]
    race_track = ""

    for i, pos in enumerate(positions):
        if pos < 0:
            pos = 0
        track[i][pos] = horses[i]

    for i, row in enumerate(track):
        race_track += f"Лошадь {i + 1}: |" + ''.join(row) + "|\n"
    return race_track


async def startup_task():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    message_tasks = []

    try:
        loop.run_until_complete(asyncio.gather(startup_task()))

    finally:
        loop.close()
