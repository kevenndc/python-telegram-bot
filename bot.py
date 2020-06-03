#coding=utf8

from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, ConversationHandler
from telegram import ChatAction, ReplyKeyboardMarkup, ReplyKeyboardRemove
import logging
import requests
from dotenv import load_dotenv
import os
import sys
from recommendation import persist_rating, is_rated, recommend, get_movie_title, get_imdb_id
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from prolog_functions import assert_rating

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
  s = requests.Session()
  retries = Retry(
    total=3,
    backoff_factor=0.1,
    status_forcelist=[ 400, 502, 503, 504 ]
  )

  s.mount('http://', HTTPAdapter(max_retries=retries))
  r = s.get(f'http://www.omdbapi.com/?apikey={OMDB_KEY}&s={query}')
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

def get_movie_info(movies_dict, display_title):
  for movie in movies_dict:
    if movie['display_title'] == display_title:
      imdbID = movie['imdbID']
      r = requests.get(f'http://www.omdbapi.com/?apikey={OMDB_KEY}&i={imdbID}')
      r = r.json()

      if (r['Response'] == 'False'):
        return False
      else:
        return {
          'title': display_title,
          'genres': r['Genre'].replace(',', '|').replace(' ', ''),
          'imdbID': r['imdbID'],
        }

def get_movie_poster(movie_id):
  imdbId = get_imdb_id(movie_id)

  r = requests.get(f'http://www.omdbapi.com/?apikey={OMDB_KEY}&i={imdbId}')
  r = r.json()

  if (r['Response'] == 'False'):
    return False
  else:
    return r['Poster']

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

  if (is_rated(title_name, update.message.from_user.id)):
    update.message.reply_text('Você já avaliou esse filme.')
    return ConversationHandler.END

  context.user_data['selected_movie'] = title_name

  text = f'Qual a sua avaliação para {title_name}? (De 0,0 a 5,0)'

  update.message.reply_text(text)

  return EVALUATE

def finaliza_avaliacao(update, context):
  context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

  rating = update.message.text
  rating = float(rating.replace(',', '.'))

  user_id = update.message.from_user.id

  movies_dict = context.user_data['movies_dict_array']
  selected_movie = context.user_data['selected_movie']  

  movie_info = get_movie_info(movies_dict, selected_movie)

  assert_rating(user_id, selected_movie, rating)
  
  persist_rating(movie_info, rating, user_id)

  del context.user_data['selected_movie']
  del context.user_data['movies_dict_array']

  update.message.reply_text('Sua avaliação foi salva')

  return ConversationHandler.END

def filme_nao_encontrado(update, context):
  update.message.reply_text('Não encontrei nenhum filme com esse nome 😥')
  return ConversationHandler.END

avaliacao_handler = ConversationHandler(
  entry_points=[CommandHandler('avaliar', avaliar, pass_args=True)],

  states={
    CHOOSING: [MessageHandler(Filters.text, seleciona_avalicao)],
    EVALUATE: [MessageHandler(Filters.regex('^([0-4][,][0-9]|5[,]0)$'), finaliza_avaliacao)]
  },

  fallbacks=[CommandHandler('avaliar', filme_nao_encontrado)]
)

def recomendacao(update, context):
  update.message.reply_text('Estou calculando algumas boa recomendações para você. Isso pode levar alguns minutos. Eu aviso quando terminar! 😉')

  recomendacoes = recommend(update.message.from_user.id, N=5)

  text = 'Terminei! Aqui estão alguma recomendações de filmes para você!\n'

  index = 1
  msg_sent = False

  for recomendacao in recomendacoes:
    if not msg_sent:
      update.message.reply_text(text)
      msg_sent = True

    movie_id = recomendacao[0]
    poster = get_movie_poster(movie_id)
    title = f'{index} - {get_movie_title(movie_id)}'
  
    context.bot.send_photo(
        chat_id=update.message.chat_id, 
        photo=poster, 
        caption=title
      )
    index += 1


start_handler = CommandHandler('start', start)
recomend_handler = CommandHandler('recomendacao', recomendacao)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(avaliacao_handler)
dispatcher.add_handler(recomend_handler)

updater.start_polling()
updater.idle()