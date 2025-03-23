from flask import Flask, request, jsonify
import mysql.connector
import random
import string
import datetime

# Function to create and return a new database connection
def create_database_connection():
    connection = mysql.connector.connect(
        host="localhost",       # Database host
        user="root",            # Database username
        password="root",        # Database password
        database="appdb"        # Database name
    )
    return connection

# Function to generate a random alphanumeric string of a given length
def get_random_string(length):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for i in range(length))

app = Flask(__name__)

# Endpoint to create a new short URL using POST method
@app.route("/shorten", methods=["POST"])
def create():
    # Get JSON data from the request
    data = request.get_json(force=True)
    
    # Validate the request body: check if 'url' key exists and is valid
    if not data or "url" not in data:
        return jsonify({"error": "Missing 'url' in request body"}), 400
    
    long_url = data["url"]
    if not isinstance(long_url, str) or not long_url.strip():
        return jsonify({"error": "Invalid URL provided"}), 400
    
    # Establish a connection to the database
    conn = create_database_connection()
    cursor = conn.cursor()
    
    # Generate a unique short code
    short_code = get_random_string(6)
    check_query = "SELECT id FROM urls WHERE shortCode = %s"
    # Loop until a unique short code is generated
    while True:
        cursor.execute(check_query, (short_code,))
        if cursor.fetchone():
            short_code = get_random_string(6)
        else:
            break
    
    # Get today's date for createdAt and updatedAt columns
    today = datetime.date.today()
    
    # SQL query to insert a new URL record into the database
    insert_query = """
        INSERT INTO urls (url, shortCode, createdAt, updatedAt, count)
        VALUES (%s, %s, %s, %s, %s)
    """
    try:
        # Execute the insert query with provided values
        cursor.execute(insert_query, (long_url, short_code, today, today, 0))
        conn.commit()  # Commit changes to the database
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        return jsonify({"error": f"Failed to insert record: {err}"}), 500
    
    # Get the id of the newly inserted record
    new_id = cursor.lastrowid
    
    # Retrieve the inserted record (optional step for confirmation)
    get_query = "SELECT id, url, shortCode, createdAt, updatedAt, count FROM urls WHERE id = %s"
    cursor.execute(get_query, (new_id,))
    row = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    # If record is successfully retrieved, return it with a 201 status code
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

# Endpoint to retrieve the original URL from a short code using GET method
@app.route("/shorten/<string:short_code>", methods=["GET"])
def retrieve_original_url(short_code):
    try:
        # Establish DB connection
        conn = create_database_connection()
        cursor = conn.cursor()
        # SQL query to select the record with the given short code
        query = "SELECT id, url, shortCode, createdAt, updatedAt, count FROM urls WHERE shortCode = %s"
        cursor.execute(query, (short_code,))
        row = cursor.fetchone()
        conn.commit()
        
        # Increment the count by 1
        update_query = "UPDATE urls SET count = count + 1 WHERE shortCode = %s"
        cursor.execute(update_query, (short_code,))
        conn.commit()
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500


    # Return the record if found, otherwise return a 404 error
    if row:
        result = {
            "id": str(row[0]),
            "url": row[1],
            "shortCode": row[2],
            "createdAt": row[3].isoformat(),
            "updatedAt": row[4].isoformat()
        }
        return jsonify(result), 200
    else:
        return jsonify({"error": "Short URL not found"}), 404

# Endpoint to update an existing short URL using the PUT method
@app.route("/shorten/<string:short_code>", methods=["PUT"])
def update_short_url(short_code):
    # Get JSON data from the request
    data = request.get_json(force=True)
    
    # Establish DB connection
    conn = create_database_connection()
    cursor = conn.cursor()
    
    # Check if the record with the given short code exists
    select_query = "SELECT id, createdAt FROM urls WHERE shortCode = %s"
    cursor.execute(select_query, (short_code,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return jsonify({"error": "Short URL not found"}), 404
    
    record_id = row[0]
    # Use today's date as the new updatedAt value
    updated_at = datetime.date.today()
    # SQL query to update the updatedAt field (and URL if necessary)
    update_query = "UPDATE urls set updatedAt = %s WHERE shortCode = %s"
    try:
        cursor.execute(update_query, (updated_at, short_code,))
        conn.commit()
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        return jsonify({"error": f"Failed to update record: {err}"}), 500
    
    # Retrieve the updated record for confirmation
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

# Endpoint to delete an existing short URL using the DELETE method
@app.route("/shorten/<string:short_code>", methods=["DELETE"])
def delete_short_url(short_code):
    # Establish DB connection
    conn = create_database_connection()
    cursor = conn.cursor()
    
    # Check if the record with the provided short code exists
    select_query = "SELECT id FROM urls WHERE shortCode = %s"
    cursor.execute(select_query, (short_code,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return jsonify({"error": "Short URL not found"}), 404
    
    # SQL query to delete the record
    delete_query = "DELETE FROM urls WHERE shortCode = %s"
    try:
        cursor.execute(delete_query, (short_code,))
        conn.commit()  # Commit the deletion
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        return jsonify({"error": f"Failed to delete record: {err}"}), 500

    cursor.close()
    conn.close()
    # Return a 204 No Content status code upon successful deletion
    return "", 204

# Endpoint to get statistics for a short URL using the GET method
@app.route("/shorten/<string:short_code>/stats", methods=["GET"])
def get_stats(short_code):
    try:
        conn = create_database_connection()
        cursor = conn.cursor()
        # Query to retrieve record with the given short code
        query = "SELECT id, url, shortCode, createdAt, updatedAt, count FROM urls WHERE shortCode = %s"
        cursor.execute(query, (short_code,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500

    if row:
        # Map the database column 'count' to 'accessCount' in the response
        result = {
            "id": str(row[0]),
            "url": row[1],
            "shortCode": row[2],
            "createdAt": row[3].isoformat(),
            "updatedAt": row[4].isoformat(),
            "accessCount": row[5]
        }
        return jsonify(result), 200
    else:
        return jsonify({"error": "Short URL not found"}), 404


if __name__ == "__main__":
    # Run the Flask application in debug mode
    app.run(debug=True)
