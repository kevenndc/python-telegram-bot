import requests

def assert_rating(user_id, movie_title, rating):
  data = {
    'userId' : user_id,
    'movieTitle' : movie_title,
    'rating': rating
  }

  url = 'http://localhost:3333/rate'

  response = requests.post(url, data=data)

  return