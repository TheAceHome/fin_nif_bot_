# -*- coding: utf8 -*-
import json
from datetime import datetime

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton
import asyncio
import aioschedule
import pandas as pd
import yfinance as yf

import graphics
import strategy_final
import subs

API_TOKEN = '1126013987:AAGc1GzxCvdPf6KZBxAPXP7y_4ZoFEtDlbo'
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class Form(StatesGroup):
    ticker = State()
    start_date = State()
    end_date = State()
    graph_type = State()
    mva = State()
    mva2 = State()
    stop3 = State()
    subs_ticker = State()
    sma = State()
    tick2 = State()


class DateTimeException(Exception):
    print("DateTimeException")
    pass


class FutureDataDoesNotExistsException(Exception):
    print("FutureDataDoesNotExistsException")
    pass


class FirstDateBiggerThanSecondException(Exception):
    print("FirstDateBiggerThanSecondException")
    pass


class DatesCannotBeEqualException(Exception):
    print("DatesCannotBeEqualException")
    pass


class TickerDoesNotExistsException(Exception):
    print("TickerDoesNotExistsException")
    pass


class GraphDoesNotExistsException(Exception):
    print("GraphDoesNotExistsException")
    pass


class SmaValuesException(Exception):
    print("SmaValuesException")
    pass


def check_first_date(date):
    try:
        d = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise DateTimeException()

    if d > datetime.now():
        raise FutureDataDoesNotExistsException()
    return date


def check_second_date(date1, date2):
    try:
        d2 = datetime.strptime(date2, '%Y-%m-%d')
    except ValueError:
        raise DateTimeException()

    d1 = datetime.strptime(date1, '%Y-%m-%d')

    if d1 > d2:
        raise FirstDateBiggerThanSecondException()

    if d2 > datetime.now():
        raise FutureDataDoesNotExistsException()

    return date2


def check_ticker(ticker):
    t = yf.Ticker(ticker)
    if t.info['regularMarketPrice'] is None:
        raise TickerDoesNotExistsException()
    return ticker


def check_graph(graph):
    if graph not in ["candle", "line", "renko"]:
        raise GraphDoesNotExistsException()
    return graph


def check_sub_tickers(tickers):
    for ticker in tickers.split(","):
        check_ticker(ticker)
    return tickers.lower()


def check_sub_sma_values(tickers, sma):
    if len(sma.split(" ")) == 1:
        return " ".join(sma.split(" ") * len(tickers.split(",")))
    elif len(sma.split(" ")) == len(tickers.split(",")):
        return sma
    else:
        raise SmaValuesException()


candle_button = KeyboardButton('candle')
line_chart_button = KeyboardButton('line')
renko_button = KeyboardButton('renko')
graphic_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(candle_button,
                                                                                         line_chart_button,
                                                                                         renko_button)


def check_sma_values(sma):
    s = sma.split(",")
    if not s[0].isdigit() or not s[1].isdigit():
        raise SmaValuesException
    return sma


@dp.message_handler(commands=['cancel'], state=Form.all_states)
async def process_start_command(message: types.Message, state: FSMContext):
    await state.reset_state()
    await bot.send_message(message.from_user.id,
                           text=MESSAGES["cancel"],
                           parse_mode='HTML',
                           reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await bot.send_message(message.from_user.id,
                           text=MESSAGES['start'])


@dp.message_handler(commands=['plots'])
async def handle_text(message: types.Message, state: FSMContext):
    try:
        await Form.ticker.set()
        print(state.proxy().state)
        async with state.proxy() as data:
            data['initiator'] = "plots"
        await bot.send_message(message.from_user.id,
                               text=MESSAGES['ticker'],
                               parse_mode='HTML')

    except:
        print('Ошибка в части plot')


@dp.message_handler(commands=['signals'])
async def handle_text(message: types.Message, state: FSMContext):
    try:
        await Form.ticker.set()
        async with state.proxy() as data:
            data['initiator'] = "signals"
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["ticker"],

                               parse_mode='HTML')
    except:
        print('Ошибка в части signals')


@dp.message_handler(commands=['strategy'])
async def handle_text(message: types.Message, state: FSMContext):
    try:
        await Form.ticker.set()
        async with state.proxy() as data:
            data['initiator'] = "strategy"
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["ticker"],
                               parse_mode='HTML')
    except:
        print('Ошибка в части strategy')


@dp.message_handler(state=Form.ticker)
async def process_name(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['ticker'] = check_ticker(message.text)
        await Form.start_date.set()
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["ticker_period_start"],
                               parse_mode='HTML')

    except TickerDoesNotExistsException:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["ticker_error"],
                               parse_mode='HTML')
    except:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["general_error"],
                               parse_mode='HTML')


@dp.message_handler(state=Form.start_date)
async def process_name(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['start'] = check_first_date(message.text)
        if data['initiator'] != "strategy":
            await Form.end_date.set()
        else:
            await Form.stop3.set()
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["ticker_period_end"],
                               parse_mode='HTML')

    except DateTimeException:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["ticker_period_error"],
                               parse_mode='HTML')

    except FutureDataDoesNotExistsException:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["ticker_period_future_error"],
                               parse_mode='HTML')

    except:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["general_error"],
                               parse_mode='HTML')


@dp.message_handler(state=Form.end_date)
async def process_name(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['stop'] = check_second_date(data['start'], message.text)
        if data['initiator'] == "plots":
            await Form.graph_type.set()
            await bot.send_message(message.from_user.id,
                                   text=MESSAGES["ticker_graphic"],
                                   parse_mode='HTML',
                                   reply_markup=graphic_keyboard)
        else:
            await Form.mva2.set()
            await bot.send_message(message.from_user.id,
                                   text=MESSAGES["sma_value"],
                                   parse_mode='HTML')
    except DateTimeException:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["ticker_period_error"],
                               parse_mode='HTML')

    except FirstDateBiggerThanSecondException:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["ticker_wrong_period_error"],
                               parse_mode='HTML')

    except FutureDataDoesNotExistsException:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["ticker_period_future_error"],
                               parse_mode='HTML')

    except:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["general_error"],
                               parse_mode='HTML')


@dp.message_handler(state=Form.graph_type)
async def process_name(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['graph_type'] = check_graph(message.text)
        await Form.mva.set()
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["sma_value"],
                               parse_mode='HTML',
                               reply_markup=types.ReplyKeyboardRemove())

    except GraphDoesNotExistsException:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["ticker_graphic_error"],
                               parse_mode='HTML')
    except:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["general_error"],
                               parse_mode='HTML')


@dp.message_handler(state=Form.mva)
async def process_gender(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['mva'] = check_sma_values(message.text)
            mva = tuple(int(i) for i in list(data['mva'].split(',')))
        graphics.plot_japan(data['ticker'], data['start'], data['stop'], data['graph_type'], mva)
        await bot.send_photo(message.from_user.id, open('graphs/japan.png', 'rb'))
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["suggest_notification"])
        await bot.send_message(message.from_user.id, text=MESSAGES["start_help"])
        await state.finish()

    except SmaValuesException:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["sma_value_error"],
                               parse_mode='HTML')

    except:
        await state.finish()
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["general_error"],
                               parse_mode='HTML')


# signals
@dp.message_handler(state=Form.mva2)
async def process_gender(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['mva2'] = message.text
        mva = tuple(int(i) for i in list(data['mva2'].split(',')))
        graphics.signals(data['ticker'], data['start'], data['stop'], mva)
        await bot.send_photo(message.from_user.id, open('graphs/signals.png', 'rb'))
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["suggest_notification"])
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["start_help"])
        await state.finish()


####Backtesting####
@dp.message_handler(state=Form.stop3)
async def process_name(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['stop'] = check_second_date(data['start'], message.text)
        strategy_final.strategy(data['ticker'], data['start'], data['stop'])
        await bot.send_document(message.from_user.id, open('db/result.csv', 'rb'))
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["suggest_notification"])
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["start_help"])
        await state.finish()

    except DateTimeException:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["ticker_period_error"],
                               parse_mode='HTML')

    except FirstDateBiggerThanSecondException:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["ticker_wrong_period_error"],
                               parse_mode='HTML')

    except FutureDataDoesNotExistsException:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["ticker_period_future_error"],
                               parse_mode='HTML')

    except:
        await state.finish()
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["general_error"],
                               parse_mode='HTML')


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await bot.send_message(message.from_user.id,
                           text=MESSAGES["help"])


###Подписка###
@dp.message_handler(commands=['subscribe'])
async def handle_text(message: types.Message):
    try:
        await Form.subs_ticker.set()
        await bot.send_message(message.from_user.id,
                               text=MESSAGES['subscribe'],
                               parse_mode='HTML')
    except:
        print('Ошибка в части subscribe')


@dp.message_handler(state=Form.subs_ticker)
async def process_name(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['subs_ticker'] = check_sub_tickers(message.text)
            data['userid'] = message.from_user.id
        await Form.sma.set()
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["sma_value_sub"],
                               parse_mode='HTML')

    except TickerDoesNotExistsException:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["sub_tickers_error"],
                               parse_mode='HTML')
    except:
        await state.finish()
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["general_error"],
                               parse_mode='HTML')


@dp.message_handler(state=Form.sma)
async def process_name(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['sma'] = check_sub_sma_values(data['subs_ticker'], message.text)
        subs.set_tickers(data['userid'], data['subs_ticker'], data['sma'])
        await state.finish()
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["subscribe_success"],
                               parse_mode='HTML')
    except SmaValuesException:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["sma_value_sub_error"],
                               parse_mode='HTML')
    except:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["general_error"],
                               parse_mode='HTML')


@dp.message_handler(commands=['sublist'])
async def process_help_command(message: types.Message):
    m = subs.sub_ticker_list(message.from_user.id)
    await bot.send_message(message.from_user.id,
                           text=MESSAGES["user_sub_list"]+m)


# Отписка
@dp.message_handler(commands=['unsubscribe'])
async def handle_text(message: types.Message):
    try:
        await Form.tick2.set()
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["unsub"],
                               parse_mode='HTML')
    except:
        print('Ошибка в части unsubscribe')


@dp.message_handler(state=Form.tick2)
async def process_name(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['userid'] = message.from_user.id
            data['tick2'] = message.text
        subs.del_tic(data['userid'], data['tick2'])
        await state.finish()
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["unsub_success"],
                               parse_mode='HTML')
    except:
        await state.finish()
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["general_error"],
                               parse_mode='HTML')


###Отправка индикаторов###
async def send_indicator():
    strategy_final.comp_strategy()
    df = pd.read_csv('db/database.csv', header=0, sep=';')
    for user_id in df['user_id'].unique():
        u_data = df[df['user_id'] == user_id][['tickers', 'actions_all']]
        msg = "\n".join([f"{d[0]} - {d[1]}" for d in u_data.values])
        await bot.send_message(user_id, text=msg)


async def scheduler():
    aioschedule.every().day.at("09:45").do(send_indicator)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())
    print("Bot started")


if __name__ == '__main__':
    with open("messages/reply_messages.json", "r", encoding="utf-8") as f:
        MESSAGES = json.load(f)
    executor.start_polling(dp, skip_updates=False,
                           on_startup=on_startup)
