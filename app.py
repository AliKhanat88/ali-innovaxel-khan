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

@app.route("/shorten", methods=["POST", "GET"])
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
        html_form = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Create Short URL</title>
            </head>
            <body>
                <h1>Create a Short URL</h1>
                <form id="urlForm">
                    <label for="url">Enter URL:</label>
                    <input type="text" id="url" name="url" required>
                    <button type="submit">Submit</button>
                </form>
                <div id="result"></div>
                
                <script>
                document.getElementById("urlForm").addEventListener("submit", function(event) {
                    event.preventDefault();
                    var urlValue = document.getElementById("url").value;
                    fetch("/shorten", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({ url: urlValue })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if(data.error) {
                            document.getElementById("result").innerHTML = "<p style='color:red;'>" + data.error + "</p>";
                        } else {
                            document.getElementById("result").innerHTML = 
                                "<p>Short URL created:</p>" +
                                "<ul>" +
                                "<li>ID: " + data.id + "</li>" +
                                "<li>URL: " + data.url + "</li>" +
                                "<li>Short Code: " + data.shortCode + "</li>" +
                                "<li>Created At: " + data.createdAt + "</li>" +
                                "<li>Updated At: " + data.updatedAt + "</li>" +
                                "<li>Count: " + data.count + "</li>" +
                                "</ul>";
                        }
                    })
                    .catch(error => {
                        document.getElementById("result").innerHTML = "<p style='color:red;'>Error: " + error + "</p>";
                    });
                });
                </script>
            </body>
            </html>
            """
        return html_form

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

if __name__ == "__main__":
    app.run(debug=True)
