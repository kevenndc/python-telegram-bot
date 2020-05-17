#coding=utf8

from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, ConversationHandler
from telegram import ChatAction, ReplyKeyboardMarkup, ReplyKeyboardRemove
import logging
import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

OMDB_KEY = '1d4c1640'
title_name = ''

CHOOSING, EVALUATE, FINISHING_EVALUATION = range(3)


updater = Updater(token='1190067969:AAFHaVBG7JKcMv3XWqRneJeDE68vpqhPISU', use_context=True)
dispatcher = updater.dispatcher


def start(update, context):
  context.bot.send_message(chat_id=update.effective_chat.id, text="Eu sou um bot, por favor, fale comigo!")


def get_movie_title(query):
  titles = []
  r = requests.get(f'http://www.omdbapi.com/?apikey={OMDB_KEY}&s={query}')
  r = r.json()

  if r['Response'] == 'False':
    return False
  else:
    search_results = r['Search']

    for result in search_results:
      title = result['Title']
      titles.append(title)

    return titles
  

def avaliar(update, context):
  bot_context = context.bot
  bot_context.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

  query = '+'.join(context.args)

  titles = get_movie_title(query)

  if not titles: 
    update.message.reply_text('Não encontrei nenhum filme com esse nome 😥')
    return ConversationHandler.END

  titles = [[title] for title in titles]

  reply_keyboard = titles

  text = 'Qual destes filmes você quer avaliar?'

  update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

  return CHOOSING

def seleciona_avalicao(update, context):
  context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

  title_name = update.message.text

  text = f'Qual a sua avaliação para {title_name}?'
  
  reply_keyboard = [['Gostei 👍'], ['Não gostei 👎']]

  update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

  return EVALUATE

def finaliza_avaliacao(update, context):
  context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

  #context.user_data

  update.message.reply_text('Sua avaliação foi salva')

  return ConversationHandler.END

def filme_nao_encontrado(update, context):
  update.message.reply_text('Não encontrei nenhum filme com esse nome 😥')
  return ConversationHandler.END

avaliacao_handler = ConversationHandler(
  entry_points=[CommandHandler('avaliar', avaliar, pass_args=True)],

  states={
    CHOOSING: [MessageHandler(Filters.text, seleciona_avalicao)],
    EVALUATE: [MessageHandler(Filters.text, finaliza_avaliacao)]
  },

  fallbacks=[CommandHandler('avaliar', filme_nao_encontrado)]
)

start_handler = CommandHandler('start', start)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(avaliacao_handler)

updater.start_polling()
updater.idle()