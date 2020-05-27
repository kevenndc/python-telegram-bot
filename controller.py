import pandas as pd
import requests
import os
from dotenv import load_dotenv
#from recommendation import map_similarity

#carrega as variaveis de ambiente
load_dotenv()

OMDB_KEY = os.getenv('OMDB_KEY')

idx = pd.IndexSlice

#Iniciado o dataset
links = pd.read_csv('./dataset/links.csv', index_col=['movieId'])
movies = pd.read_csv('./dataset/movies.csv', sep=',', index_col=['movieId'])
ratings = pd.read_csv('./dataset/ratings.csv', index_col=['userId', 'movieId'])
tags = pd.read_csv('./dataset/tags.csv', index_col=['userId', 'movieId'])

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

def persist_new_movie(movie_id, movie_info):
  title, genres, imdbId = movie_info.values()

  #Adiciona novo filme no arquivo 'movies.csv'
  new_movie = {
    'movieId': [movie_id],
    'title': [title],
    'genres': [genres]
  }

  df = pd.DataFrame(new_movie, columns=['movieId', 'title', 'genres'])
  df.set_index('movieId', inplace=True)

  df.to_csv('./dataset/movies.csv', mode='a', header=None)

  #Adiciona os dados do filme em 'links.csv'
  new_link = {
    'movieId': [movie_id],
    'imdbId': [imdbId.replace('t', '')],
    'tmdbId': ['000000']
  }

  df = pd.DataFrame(new_link, columns=['movieId', 'imdbId', 'tmdbId'])
  df.set_index('movieId', inplace=True)

  df.to_csv('./dataset/links.csv', mode='a', header=None)

def persist_new_rating(user_id, movie_id, rating):
  
  new_rating = {
    'userId': [user_id],
    'movieId': [movie_id],
    'rating': [rating],
    'timestamp': ['000000']
  }

  df = pd.DataFrame(new_rating, columns=['userId', 'movieId', 'rating', 'timestamp'])
  df.set_index('userId', inplace=True)
  df.to_csv('./dataset/ratings.csv', mode='a', header=None)

  map_similarity(override=True)

def persist_rating(movies_dict, movie_title, rating, user_id):

  if movie_title in movies.values:
    [movie_id] = movies.loc[movies.isin([movie_title]).any(axis=1)].index.tolist()
  else:
    movie_info = get_movie_info(movies_dict, movie_title)
    movie_id = movies.last_valid_index() + 1

    persist_new_movie(movie_id, movie_info)

  persist_new_rating(user_id, movie_id, rating)

def get_imdb_id(movie_id):
  imdbId = int(links.loc[idx[movie_id], 'imdbId'])

  return f'tt{imdbId}'
