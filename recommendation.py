import pandas as pd
import math
import numpy as np 
import operator
import joblib
import os.path

idx = pd.IndexSlice

#Iniciado o dataset
links = pd.read_csv('./dataset/links.csv', index_col=['movieId'])
movies = pd.read_csv('./dataset/movies.csv', sep=',', index_col=['movieId'])
ratings = pd.read_csv('./dataset/ratings.csv', index_col=['userId', 'movieId'])
tags = pd.read_csv('./dataset/tags.csv', index_col=['userId', 'movieId'])

def get_movies_by_user(user_id, rating_cut=0, _list=False):

  """Retorna a lista de filmes avaliados por um usuário

    Keyword arguments:
    user_id -- id do usuário
    rating_cut -- retorna só itens avaliados com rating maior que rating_cut (default: 0)
    _list -- se True retorna somente os ids dos filmes, se False retorna os ids com o valor do rating (default: False)
    
  """

  movie_dict = {}
  rating_dict = ratings.loc[idx[user_id, :], 'rating'].T.to_dict()

  for item in rating_dict:
    if rating_cut != 0:
      if rating_dict[item] >= rating_cut:
        movie_dict[item[1]] = [rating_dict[item]]

    else:
      movie_dict[item[1]] = rating_dict[item]

  if _list:
    return list(movie_dict.keys())

  return movie_dict

def get_users_by_movie(movie_id, rating_cut=0, _list=False):

  """Retorna a lista de usuários que avaliaram determinado filme

    Keyword arguments:
    movie_id -- id do filme
    rating_cut -- retorna só usuários que avaliaram o filme com rating maior que rating_cut (default: 0)
    _list -- se True retorna somente os ids dos usuários, se False retorna os ids com o valor do rating
    
  """

  user_dict = {}
  rating_dict = ratings.loc[idx[:, movie_id], 'rating'].T.to_dict()

  for item in rating_dict:
    if rating_cut != 0:
      if rating_dict[item] >= rating_cut:
        user_dict[item[0]] = rating_dict[item]

    else:
      user_dict[item[0]] = rating_dict[item]

  if _list:
    return list(user_dict.keys())

  return user_dict

def get_rating_by_user_movie(user_id, movie_id):

  """Retorna o rating que o usuário (user_id) deu para um filme (movie_id). Se não existir, retorna 0.0.

    Keyword arguments:
    user_id -- id do usuário
    movie_id -- id do filme
    
  """

  rating = 0.0

  try:
    rating = ratings.loc[idx[user_id, movie_id], 'rating']

  except KeyError:
    rating = 0.0

  return rating


def get_all_users():

  """Retorna o id de todos os usuários.
    
  """

  users_id = [i[0] for i in ratings.index.values]

  return list(set(users_id))

def get_movie_title(movie_id):

  """Retorna o título de um filme.

    Keyword arguments:
    movie_id -- id do filme
    
  """
  info = movies.loc[idx[movie_id], :]

  return info['title']

#Testes

all_users = get_all_users()

user_movies_dict = {}
user_movies_list = {}

for user in all_users:
  user_movies_dict[user] = get_movies_by_user(user, _list=False)
  user_movies_list[user] = list(user_movies_dict[user])


def intersect_items(x_user_id, y_user_id):

  """Retorna duas listas de ratings. Os ratings correspondem aos itens avaliados por x e y.
        É retornada duas listas distintas já que os itens são os mesmo, mas as avaliações são distintas.
        Isso irá facilitar na hora de calcuar a similaridade dos usuários.

    Keyword arguments:
    x_user_id -- id do usuário x
    y_user_id -- id do usuário y
    
  """

  dict_x = user_movies_dict[x_user_id]
  dict_y = user_movies_dict[y_user_id]

  all_keys = set(list(dict_x.keys()) + list(dict_y.keys()))

  x_ratings = []
  y_ratings = []

  for key in all_keys:
    if key in dict_x and key in dict_y:
      x_ratings.append(dict_x[key])
      y_ratings.append(dict_y[key])

  x_ratings = np.array(x_ratings)
  y_ratings = np.array(y_ratings)

  return x_ratings, y_ratings

def similarity(x_user_id, y_user_id):
  """Retorna a similaridade de dois usuários baseada nos ratings dos filmes

    Keyword arguments:
    x_user_id -- id do usuário x
    y_user_id -- id do usuário y
    
  """

  x_ratings, y_ratings = intersect_items(x_user_id, y_user_id)

  if len(x_ratings) == 0 or (len(y_ratings)) == 0:
    return 0.0

  x_mean_ratings = np.mean(x_ratings)
  y_mean_ratings = np.mean(y_ratings)

  numerator = (x_ratings - x_mean_ratings) * (y_ratings - y_mean_ratings)
  numerator = np.sum(numerator)

  x_den = np.sum(np.power(x_ratings - x_mean_ratings, 2))
  y_den = np.sum(np.power(y_ratings - y_mean_ratings, 2))

  similarity_value = numerator / np.sqrt(x_den * y_den)

  return similarity_value

def map_similarity(override=False):

  if os.path.exists('./dataset/users_similarity.pkl') and not override:
    return

  similarity_map = {}

  all_users = get_all_users()

  for x_user in all_users:
    for y_user in all_users:
      if x_user < y_user:
        similarity_map[(x_user, y_user)] = similarity(x_user, y_user)

  joblib.dump(similarity_map, './dataset/users_similarity.pkl')

map_similarity()

user_similarity = joblib.load('./dataset/users_similarity.pkl')

def get_top_neighbors_rated_item(user_id, movie_id, N):
  """Retorna os N usuários mais similares a id_user que avaliram o id_item

    Keyword arguments:
    user_id -- id do usuário
    movie_id -- id do filme
    N -- Número de usuários semelhantes retornados. 
    
  """
  
  all_users = get_all_users()
  similars = {}

  for user in all_users:
    user_items = user_movies_list[user]

    if user_id != user and movie_id in user_items:
      similars[(user_id, user)] = user_similarity[(user_id, user)]

  sorted_similars = sorted(similars.items(), key=operator.itemgetter(1), reverse=True)

  return sorted_similars[:N]

def predict_rating(user_id, movie_id, N=20):

  """Retorna o possível rating de um usuário baseado em ratings de usuários simialres

    Keyword arguments:
    user_id -- id do usuário
    movie_id -- id do filme
    N -- Número de usuários semelhantes. 
    
  """

  user_items = user_movies_dict[user_id]
  all_user_values = [user_items[i] for i in user_items]
  user_mean = np.mean(all_user_values)

  topN_users = get_top_neighbors_rated_item(user_id, movie_id, N)

  _sum = 0
  _sum_k = 0

  for user in topN_users:
    similarity = user[1]
    user_u = user[0][1]

    user_u_rating = get_rating_by_user_movie(user_u, movie_id)

    user_u_items = user_movies_dict[user_u]

    all_user_u_values = [user_u_items[i] for i in user_u_items]

    user_u_mean = np.mean(all_user_u_values)

    _sum += similarity * (user_u_rating - user_u_mean)
    _sum_k += abs(similarity)

  if _sum_k == 0:
    k = 0
  else:
    k = 1 / _sum_k

  final_rating = user_mean + k * _sum

  return final_rating

def recommend(user_id, N=10):

  all_movies = list(movies.index.values)
  all_user_movies = get_movies_by_user(user_id, _list=True)

  movies_to_predict = [movie for movie in all_movies if movie not in all_user_movies]

  predicts = {}

  for movie in movies_to_predict:
    rating = predict_rating(user_id, movie)

    if rating:
      predicts[movie] = rating

  sorted_movies = sorted(predicts.items(), key=operator.itemgetter(1), reverse=True)

  return sorted_movies[:N]

#Teste
count = 1
top10 = recommend(1, 10)
print("Filmes recomendados para o usuário 1:")

for movie in top10:
  print("\t %.2d" % count, "[%.1f]" % movie[1], get_movie_title(movie[0]))
  count += 1