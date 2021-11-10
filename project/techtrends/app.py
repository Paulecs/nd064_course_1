import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
from collections import defaultdict

import logging
import sys
import os


# Function to get a database connection.
# This function connects to database with the name `database.db`
connection_counter = 0

def get_db_connection():
    global connection_counter
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    connection_counter+= 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    app.logger.info('Article; "{}" is retrieved'.format(post['title']))
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the Health / Status endpoint
#  to return the following respones
   ## An HTTP 200 status code
   ## A JSON response containing the result: OK - healthy message
@app.route('/healthz')

def healthz():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )

    ## log line
    app.logger.info('Status request successful')
    return response

# Build a /metrics endpoint that would return the following:
  ## An HTTP 200 status code
  ## A JSON response with the following metrics:
  ## Total amount of posts in the database
  ## Total amount of connections to the database. For example, accessing an article will query the database, hence will count as a connection.
@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    response = app.response_class(
            response=json.dumps({"status":"success","code":0,"data":{"db_connetion_count": connection_counter,"post_count":len(posts)}}),
            status=200,
            mimetype='application/json'
    )
    ## log line
    
    return response

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.info("%s The Article requested does not exist")
      return render_template('404.html'), 404
    else:
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('The "About Us page" is retrieved.')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        app.logger.info("Article; '{}' is created".format(title))
        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            return redirect(url_for('index'))

    return render_template('create.html')

# start the application on port 3111
if __name__ == "__main__":

#Set up logging
    logger = logging.getLogger('app_logger')

    #Set loglevel to an Environment Variable
    loglevel = os.getenv("APP_LOGGERLEVEL", "DEBUG").upper()

    #Define logging output by loglevel and Assign handlers
    loglevel = (
        getattr(logging, loglevel)
        if loglevel in ["CRITICAL", "DEBUG", "ERROR", "INFO", "WARNING"]
        else logging.DEBUG
        )
    # standard_out (stdout)
    standard_out = logging.StreamHandler(sys.stdout)

    #Set the lowest threshold that gets logged to stdout
    standard_out.setLevel(loglevel)

    #standard_error (stderr)
    standard_error = logging.StreamHandler(sys.stderr)

    #Set the lowest threshold that gets logged to stderr
    standard_error.setLevel(logging.ERROR)

    #Add handlers to our logger
    logger.addHandler(standard_out)
    logger.addHandler(standard_error)

    handlers = [standard_out, standard_error]

    #Assign logging defaults
    logging.basicConfig(level = logging.DEBUG,
        handlers=handlers, format='%(levelname)s:%(name)s: %(asctime)s,  %(message)s')

    app.run(host='0.0.0.0', port='3111')