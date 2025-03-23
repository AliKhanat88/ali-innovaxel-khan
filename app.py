from flask import Flask
import mysql.connector

def create_database_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="appdb"
    )
    return connection

app = Flask(__name__)

@app.route("/")
def home():
    connection = create_database_connection()
    cursor = connection.cursor()
    cursor.execute("select * from urls")
    for row in cursor:
        print(row)
    cursor.close()
    connection.close()
    return "Hello World"

if __name__ == "__main__":
    app.run(debug=True)