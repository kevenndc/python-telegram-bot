#coding=utf8

from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, ConversationHandler
from telegram import ChatAction, ReplyKeyboardMarkup, ReplyKeyboardRemove
import logging
import requests
from dotenv import load_dotenv
import os
import sys
from controller import persist_rating

#carrega as variaveis de ambiente
load_dotenv()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

OMDB_KEY = os.getenv('OMDB_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

title_name = ''

CHOOSING, EVALUATE = range(2)

updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher


def start(update, context):
  context.bot.send_message(chat_id=update.effective_chat.id, text="Eu sou um bot, por favor, fale comigo!")

def get_movies(query):
  r = requests.get(f'http://www.omdbapi.com/?apikey={OMDB_KEY}&s={query}')
  r = r.json()

  if r['Response'] == 'False':
    return False
  else:
    search_results = r['Search']
    return search_results

def get_titles(movies):
  titles = []

  for movie in movies:
    title = f'{movie["Title"]} ({movie["Year"]})'
    movie['display_title'] = title
    titles.append(title)
 
  return titles
  

def avaliar(update, context):
  bot_context = context.bot
  bot_context.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

  query = '+'.join(context.args)
  movies = get_movies(query)
  titles = get_titles(movies)

  context.user_data['movies_dict_array'] = movies

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

  context.user_data['selected_movie'] = title_name

  text = f'Qual a sua avaliação para {title_name}?'

  update.message.reply_text(text)

  return EVALUATE

def finaliza_avaliacao(update, context):
  context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

  rating = update.message.text
  rating = float(rating.replace(',', '.'))

  user_id = update.message.from_user.id

  movies_dict = context.user_data['movies_dict_array']
  selected_movie = context.user_data['selected_movie']  
  
  persist_rating(movies_dict, selected_movie, rating, user_id)

  del context.user_data['selected_movie']
  del context.user_data['movies_dict_array']

  # try:
  #   evaluated = context.user_data['evaluated_movies']
  #   context.user_data['evaluated_movies'] = [*evaluated, movie]
    
  # except KeyError:
  #   context.user_data['evaluated_movies'] = [movie]

  # print(context.user_data['evaluated_movies'])

  update.message.reply_text('Sua avaliação foi salva')

  return ConversationHandler.END

def filme_nao_encontrado(update, context):
  update.message.reply_text('Não encontrei nenhum filme com esse nome 😥')
  return ConversationHandler.END

avaliacao_handler = ConversationHandler(
  entry_points=[CommandHandler('avaliar', avaliar, pass_args=True)],

  states={
    CHOOSING: [MessageHandler(Filters.text, seleciona_avalicao)],
    EVALUATE: [MessageHandler(Filters.regex('(([0-5][,]?)[0-9])'), finaliza_avaliacao)]
  },

  fallbacks=[CommandHandler('avaliar', filme_nao_encontrado)]
)

start_handler = CommandHandler('start', start)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(avaliacao_handler)

updater.start_polling()
updater.idle()