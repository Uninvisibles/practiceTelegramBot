from aiogram import Bot
from aiogram import Dispatcher
from aiogram import executor
from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import CallbackQuery
from aiogram.types import Message
from json import dumps
from json import loads
from json import load
import db
import config

questions = load(open("questions.json", "r", encoding="utf-8"))

bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot=bot)


def compose_markup(question: int):
    km = InlineKeyboardMarkup(row_width=3)
    for i in range(len(questions[question]["variants"])):
        cd = {
            "question": question,
            "answer": i
        }
        km.insert(InlineKeyboardButton(questions[question]["variants"][i], callback_data=dumps(cd)))
    return km


def reset(uid: int):
    db.set_in_process(uid, False)
    db.change_questions_passed(uid, 0)
    db.change_questions_message(uid, 0)
    db.change_current_question(uid, 0)


@dp.callback_query_handler(lambda c: True)
async def answer_handler(callback: CallbackQuery):
    data = loads(callback.data)
    q = data["question"]
    is_correct = questions[q]["correct_answer"] - 1 == data["answer"]
    passed = db.get_questions_passed(callback.from_user.id)
    msg = db.get_questions_message(callback.from_user.id)
    if is_correct:
        passed += 1
        db.change_questions_passed(callback.from_user.id, passed)
    if q + 1 > len(questions) - 1:
        reset(callback.from_user.id)
        await bot.delete_message(callback.from_user.id, msg)
        await bot.send_message(
            callback.from_user.id,
            f"🎉 *Поздравляю*, тест пройден\\.\n✅ Правильных ответов\\: *{passed} из {len(questions)}*\\.\n\n🔄 *Пройти тест снова* \\- /play", parse_mode="MarkdownV2"
        )
        return
    await bot.edit_message_text(
        questions[q + 1]["text"],
        callback.from_user.id,
        msg,
        reply_markup=compose_markup(q + 1),
        parse_mode="MarkdownV2"
    )


@dp.message_handler(commands=["play"])
async def go_handler(message: Message):
    if not db.is_exists(message.from_user.id):
        db.add(message.from_user.id)
    if db.is_in_process(message.from_user.id):
        await bot.send_message(message.from_user.id, "🚫 Вы не сможете начать тест *вы уже проходите его*\\.", parse_mode="MarkdownV2")
        return
    db.set_in_process(message.from_user.id, True)
    msg = await bot.send_message(
        message.from_user.id,
        questions[0]["text"],
        reply_markup=compose_markup(0),
        parse_mode="MarkdownV2"
    )
    db.change_questions_message(message.from_user.id, msg.message_id)
    db.change_current_question(message.from_user.id, 0)
    db.change_questions_passed(message.from_user.id, 0)


@dp.message_handler(commands=["finish"])
async def quit_handler(message: Message):
    if not db.is_in_process(message.from_user.id):
        await bot.send_message(message.from_user.id, "❗️ Вы ещё *не начали тест*\\.", parse_mode="MarkdownV2")
        return
    reset(message.from_user.id)
    await bot.send_message(message.from_user.id, "✅ Вы успешно *закончили тест*\\.", parse_mode="MarkdownV2")


@dp.message_handler(commands=["start"])
async def start(message: Message):
    await message.answer("👋 *Привет\\!* \n\n📝 Я бот для теста, предлагаю тебе пройти небольшой опрос, который проверит твои знания\\. \n\n📝 Для успешного прохождения теста нужно ответить на *10 вопросов*\\. \n\n⁉️ На каждый вопрос дается три варианта ответа, вам нужно выбрать один из них\\. \n\n*Начать тест* \\- /play\n*Закончить тест* \\- /finish\n*Помощь* \\- /help", parse_mode="MarkdownV2")


@dp.message_handler(commands=['help'])
async def cmd_answer(message: Message):
    await message.answer("⁉️<b> Если у вас проблемы с тестом.</b> \n✉️ <b>Напишите мне</b> <a href='https://t.me/murzakov_av'>@murzakov_av</a><b>.</b>", disable_web_page_preview=True, parse_mode="HTML")
    

def main() -> None:
    executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    main()
