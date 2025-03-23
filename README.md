# ali-innovaxel-khan

git clone <repository-url>
cd <repository-folder>

venv\Scripts\activate


pip install flask mysql-connector-python

- Create a MySQL database (e.g., `appdb`).
- Create the `urls` table using the following SQL:
    ```sql
    CREATE TABLE urls (
        id INT AUTO_INCREMENT PRIMARY KEY,
        url VARCHAR(500) UNIQUE,
        shortCode VARCHAR(500) UNIQUE,
        createdAt DATE,
        updatedAt DATE,
        count INT
    );

- Update the connection parameters in the `create_database_connection()` function within your application code:
    def create_database_connection():
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="appdb"
        )
        return connection

- The app will start on `http://localhost:5000/`.
- You can access the HTML form at `http://localhost:5000/create` or use tools like Postman/curl to interact with the API endpoints.
