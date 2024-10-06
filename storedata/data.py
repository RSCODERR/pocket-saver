import sqlite3
from quart import Quart, request, jsonify , render_template
from quart_cors import cors
import os

app = Quart(__name__)
app = cors(app)

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('expenditure.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create the expenditures table if it doesn't exist
def create_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expenditures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    
@app.route("/templates/jindex.html")
async def jindex():
    return await render_template("/templates/jindex.html")

@app.route('/add_expenditure', methods=['POST'])
async def add_expenditure():
    try:
        data = await request.json
        category = data.get('category')
        amount = data.get('amount')

        if category and amount:
            conn = get_db_connection()
            conn.execute('INSERT INTO expenditures (category, amount) VALUES (?, ?)', (category, amount))
            conn.commit()
            conn.close()
            return jsonify({"message": "Expenditure added successfully!"}), 201
        else:
            return jsonify({"error": "Invalid data"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/predict_savings', methods=['GET'])
async def predict_savings():
    try:
        balance = float(request.args.get('balance', 0))

        # Fetch all expenditures
        conn = get_db_connection()
        expenditures = conn.execute('SELECT SUM(amount) as total_expenditure FROM expenditures').fetchone()
        conn.close()

        total_expenditure = expenditures['total_expenditure'] if expenditures['total_expenditure'] else 0

        # Assuming a simple savings prediction rule (e.g., save 20% of the remaining balance)
        if balance > 0:
            suggested_savings = balance * 0.20
            savings_tips = "Consider setting aside 20% of your balance."
            return jsonify({
                "suggested_savings": suggested_savings,
                "savings_tips": savings_tips
            })
        else:
            return jsonify({"error": "Insufficient data to analyze."}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Ensure the table is created
    create_table()
    app.run(debug=True)

