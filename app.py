from flask import Flask, request, jsonify
import mysql.connector
import random
import string
import datetime

def create_database_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="appdb"
    )
    return connection

def get_random_string(length):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for i in range(length))

app = Flask(__name__)

@app.route("/create", methods=["POST", "GET"])
def create():
    if request.method == "POST":
        data = request.get_json(force=True)
        
        # Validate the request body
        if not data or "url" not in data:
            return jsonify({"error": "Missing 'url' in request body"}), 400
        
        long_url = data["url"]
        if not isinstance(long_url, str) or not long_url.strip():
            return jsonify({"error": "Invalid URL provided"}), 400
        
        # Establish DB connection
        conn = create_database_connection()
        cursor = conn.cursor()
        
        # Generate a unique short code
        short_code = get_random_string(6)
        check_query = "SELECT id FROM urls WHERE shortCode = %s"
        while True:
            cursor.execute(check_query, (short_code,))
            if cursor.fetchone():
                short_code = get_random_string(6)
            else:
                break
        
        # Get today's date for createdAt and updatedAt
        today = datetime.date.today()
        
        # Insert new URL record
        insert_query = """
            INSERT INTO urls (url, shortCode, createdAt, updatedAt, count)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(insert_query, (long_url, short_code, today, today, 0))
            conn.commit()
        except mysql.connector.Error as err:
            cursor.close()
            conn.close()
            return jsonify({"error": f"Failed to insert record: {err}"}), 500
        
        new_id = cursor.lastrowid
        
        # Retrieve inserted record (optional)
        get_query = "SELECT id, url, shortCode, createdAt, updatedAt, count FROM urls WHERE id = %s"
        cursor.execute(get_query, (new_id,))
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if row:
            result = {
                "id": str(row[0]),
                "url": row[1],
                "shortCode": row[2],
                "createdAt": row[3].isoformat(),
                "updatedAt": row[4].isoformat(),
                "count": row[5]
            }
            return jsonify(result), 201
        else:
            return jsonify({"error": "Creation failed"}), 500

    else:
        return "Hello World"

if __name__ == "__main__":
    app.run(debug=True)
