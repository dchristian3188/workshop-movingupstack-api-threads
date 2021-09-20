import json
import os
from flask import Flask, jsonify
from flask_cors import CORS
import redis
from db import db
import mysql.connector

app = Flask(__name__)
cors = CORS(app, resources={f"*": {"origins": "*"}})

redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = os.environ.get('REDIS_PORT', '6379')
red = redis.Redis(host=redis_host, port=redis_port)

local_db = os.environ.get('LOCAL_DB', 'false') in ['True', 'true']
db_host = os.environ.get('DB_HOST', 'localhost')
db_user = os.environ.get('DB_USER', 'root')
db_passwd = os.environ.get('DB_PASSWORD', 'myAwesomePassword')
db_name = os.environ.get('DATABASE', 'mydb')


def create_db():
    mydb = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_passwd
    )

    mycursor = mydb.cursor()
    mycursor.execute(f"CREATE DATABASE IF NOT EXISTS `mydb`;")
    mycursor.execute("""
        USE `mydb`;
        CREATE TABLE IF NOT EXISTS `threads` (
            `id` int NOT NULL,
            `title` varchar(50) NOT NULL,
            `createdBy` int NOT NULL,
            PRIMARY KEY (`id`)
            );

        insert  into `threads`(`id`,`title`,`createdBy`) values
            (1,'What''s up with the Lich?',1);
            """ )
            
conn = None
if not local_db:
    try:
        conn = mysql.connector.connect(host=db_host, user=db_user, passwd=db_passwd, database=db_name)
    except:
        try:
            create_db()
            conn = mysql.connector.connect(host=db_host, user=db_user, passwd=db_passwd, database=db_name)
        except:
            print("Unable to create database to MySQl")
        print("unable to connect to MySQL")


def get_from_db(table):
    if local_db:
        return db.get(table)

    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    return cursor.fetchall()


@app.route('/api/threads', methods=['GET'], strict_slashes=False)
def threads():
    body = {}
    key = "threads"
    try:
        value = red.get(key)
        if not value:
            threads = get_from_db(key)
            red.set(key, str(json.dumps(threads)))

            body['source'] = 'database'
            body['data'] = threads
        else:
            body['source'] = 'redis'
            body['data'] = json.loads(value.decode('ascii'))
            print("Body:")
        print(body)
        return jsonify(body), 200

    except Exception as error: 
        print(error)
        return error,200
    


@app.route('/api/threads/clear-cache', methods=['GET'], strict_slashes=False)
def clear_cache():
    red.delete("users")
    red.delete("posts")
    red.delete("threads")

    return "", 200


if __name__ == '__main__':
    app.run()
