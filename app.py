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

@app.route("/shorten", methods=["POST"])
def create():
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


@app.route("/shorten/<string:short_code>", methods=["GET"])
def retrieve_original_url(short_code):
    try:
        conn = create_database_connection()
        cursor = conn.cursor()
        query = "SELECT id, url, shortCode, createdAt, updatedAt, count FROM urls WHERE shortCode = %s"
        cursor.execute(query, (short_code,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    
    if row:
        result = {
            "id": str(row[0]),
            "url": row[1],
            "shortCode": row[2],
            "createdAt": row[3].isoformat(),
            "updatedAt": row[4].isoformat(),
            "count": row[5]
        }
        return jsonify(result), 200
    else:
        return jsonify({"error": "Short URL not found"}), 404


@app.route("/shorten/<string:short_code>", methods=["PUT"])
def update_short_url(short_code):
    data = request.get_json(force=True)

    # Connect to the database
    conn = create_database_connection()
    cursor = conn.cursor()
    
    # Check if the record exists
    select_query = "SELECT id, createdAt FROM urls WHERE shortCode = %s"
    cursor.execute(select_query, (short_code,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return jsonify({"error": "Short URL not found"}), 404
    
    record_id = row[0]
    # Update the record with new URL and updated timestamp
    updated_at = datetime.date.today()
    update_query = "UPDATE urls set updatedAt = %s WHERE shortCode = %s"
    try:
        cursor.execute(update_query, (updated_at, short_code,))
        conn.commit()
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        return jsonify({"error": f"Failed to update record: {err}"}), 500
    
    # Retrieve updated record
    get_query = "SELECT id, url, shortCode, createdAt, updatedAt, count FROM urls WHERE id = %s"
    cursor.execute(get_query, (record_id,))
    updated_row = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if updated_row:
        result = {
            "id": str(updated_row[0]),
            "url": updated_row[1],
            "shortCode": updated_row[2],
            "createdAt": updated_row[3].isoformat(),
            "updatedAt": updated_row[4].isoformat(),
            "count": updated_row[5]
        }
        return jsonify(result), 200
    else:
        return jsonify({"error": "Failed to retrieve updated record"}), 500


@app.route("/shorten/<string:short_code>", methods=["DELETE"])
def delete_short_url(short_code):
    conn = create_database_connection()
    cursor = conn.cursor()
    
    # Check if the record exists
    select_query = "SELECT id FROM urls WHERE shortCode = %s"
    cursor.execute(select_query, (short_code,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return jsonify({"error": "Short URL not found"}), 404
    
    # Delete the record
    delete_query = "DELETE FROM urls WHERE shortCode = %s"
    try:
        cursor.execute(delete_query, (short_code,))
        conn.commit()
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        return jsonify({"error": f"Failed to delete record: {err}"}), 500

    cursor.close()
    conn.close()
    return "", 204



if __name__ == "__main__":
    app.run(debug=True)
