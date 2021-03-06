# timeline_with_db.py
# * Rev.1: 2020-09-24 (Thu)
# * Draft: 2020-09-21 (Mon)

# Prerequisites:
#   1. Table users has already been created in a MySQL database.
#   2. Install 
#     $ pip install sqlalchemy
#     $ pip install mysql-connector-python

from flask      import Flask, jsonify, request
from sqlalchemy import create_engine, text

def create_app( test_config = None ):
  app = Flask( __name__ )

  if test_config is None:
    app.config.from_pyfile( "config.py" )
  else:
    app.config.update( test_config )

  database = create_engine( app.config['DB_URL'], encoding='utf-8', max_overflow=0 )
  app.database = database

  return app

app = create_app()

# For debugging
#app          = Flask( __name__ )

#-------------------------
#  Function definitions  #
#-------------------------
@app.route( '/ping', methods=[ 'GET' ] )
def ping():
  return 'pong'

@app.route( '/sign-up', methods=[ 'POST' ] )
def sign_up():
  new_user    = request.json
  # For debugging
  #print( new_user )
  #created_user = new_user

  new_user_id = app.database.execute( text("""
    INSERT INTO users(
      name,
      email,
      profile,
      hashed_password
    ) VALUES (
      :name,
      :email,
      :profile,
      :password
    )
  """), new_user).lastrowid

  row = app.database.execute( text("""
    SELECT
      id,
      name,
      email,
      profile
    FROM users
    WHERE id = :user_id
  """), {
    'user_id' : new_user_id
  }).fetchone()

  # To return the result to the client
  created_user = {
    'id'      : row['id'],
    'name'    : row['name'],
    'email'   : row['email'],
    'profile' : row['profile']
  } if row else None
#  For debugging
#  created_user = new_user

  return jsonify( created_user )

@app.route( '/tweet',methods=['POST'] )
def tweet():
  user_tweet = request.json
  tweet      = user_tweet[ 'tweet' ]
  
  if len( tweet ) > 300:
    return 'Exceeded the 300 character limit', 400

  app.database.execute( text("""
    INSERT INTO tweets (
      user_id,
      tweet
    ) VALUES (
      :id,
      :tweet
    )
   """), user_tweet )

  return '', 200

@app.route( '/timeline/<int:user_id>', methods=['GET'] )
def timeline( user_id ):
  rows = app.database.execute( text("""
    SELECT
      t.user_id,
      t.tweet
    FROM tweets t
    LEFT JOIN users_follow_list ufl ON ufl.user_id = :user_id
    WHERE t.user_id = :user_id
    OR t.user_id = ufl.follow_user_id
  """), {
    'user_id' : user_id
  }).fetchall()


  timeline = [{
    'user_id' : row['user_id'],
    'tweet' : row['tweet']
  } for row in rows]

  return jsonify({
    'user_id' : user_id,
    'timeline' : timeline
  })
