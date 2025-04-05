from flask import Flask, request, render_template
from flask_mysqldb import MySQL
import ollama

app = Flask(__name__)

# 🔹 MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Rohit@424' 
app.config['MYSQL_DB'] = 'flask_db'

mysql = MySQL(app)

def convert_nl_to_sql(nl_query):
    """Converts a natural language query to SQL using LLaMA."""
    prompt = f"""
    Convert the following natural language question into a valid SQL query for MySQL.
    Only return the SQL query without any explanations or extra text.

    Database Schema:
    - users(id INT PRIMARY KEY, username VARCHAR(50), password VARCHAR(255), email VARCHAR(100))
    - grades(id INT PRIMARY KEY, user_id INT, subject VARCHAR(50), grade CHAR(1), FOREIGN KEY (user_id) REFERENCES users(id))

    Natural Language Query:
    '{nl_query}'

    SQL Query:
    """

    response = ollama.chat(model='llama3', messages=[{"role": "user", "content": prompt}])
    sql_query = response['message']['content'].strip()

    # Clean up potential formatting issues
    sql_query = sql_query.split('```sql')[-1]
    sql_query = sql_query.split('```')[0].strip()

    print(f"[DEBUG] Generated SQL Query: {sql_query}")  # Debugging Line

    return sql_query

@app.route('/', methods=['GET', 'POST'])
def home():
    results = None
    sql_query = None
    error = None

    if request.method == 'POST':
        nl_query = request.form.get('query')

        if nl_query:
            sql_query = convert_nl_to_sql(nl_query)

            try:
                cursor = mysql.connection.cursor()
                cursor.execute(sql_query)

                # ✅ Extract column names
                column_names = [desc[0] for desc in cursor.description]

                # ✅ Fetch data and convert to list of dictionaries
                rows = cursor.fetchall()
                if rows:
                    results = [dict(zip(column_names, row)) for row in rows]
                else:
                    error = "No matching data found!"

                cursor.close()
            except Exception as e:
                error = f"SQL Error: {str(e)}"
                print(f"[DEBUG] {error}")  # Debugging Line

    return render_template('index.html', query=sql_query, results=results, error=error)

if __name__ == '__main__':
    app.run(debug=True)
