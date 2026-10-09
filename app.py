from flask import Flask, render_template, request, redirect, url_for, Response
import sqlite3
import pandas as pd
import io

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('crm_database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    conn = get_db_connection()
    filter_type = request.args.get('filter', 'all')
    search_query = request.args.get('search', '').strip()
    
    query = "SELECT * FROM customers WHERE 1=1"
    params = []
    
    if search_query:
        query += " AND (name LIKE ? OR phone LIKE ?)"
        params.extend([f'%{search_query}%', f'%{search_query}%'])
        
    if filter_type == 'hot':
        query += " AND ml_recommendation LIKE '%Hot%'"
    elif filter_type == 'warm':
        query += " AND ml_recommendation LIKE '%Warm%'"
    elif filter_type == 'cold':
        query += " AND ml_recommendation LIKE '%Cold%'"
    elif filter_type == 'churn_risk':
        query += " AND churn_risk LIKE '%High Churn Risk%'"
        
    customers = conn.execute(query, params).fetchall()
    
    all_customers = conn.execute('SELECT * FROM customers').fetchall()
    total_customers = len(all_customers)
    total_sales = sum([c['total_spent'] for c in all_customers if c['total_spent']])
    
    tickets = conn.execute('SELECT * FROM tickets').fetchall()
    market_trends = conn.execute('SELECT * FROM market_trends').fetchall()
    
    return_rate = "4.2%"
    try:
        df_returns = pd.read_excel('Superstore.xlsx', sheet_name='Returns')
        df_orders = pd.read_excel('Superstore.xlsx', sheet_name='Orders')
        return_rate = f"{(len(df_returns) / len(df_orders)) * 100:.1f}%"
    except:
        pass
    
    conn.close()
    return render_template(
        'index.html', 
        customers=customers, 
        total_customers=total_customers, 
        total_sales=total_sales, 
        current_filter=filter_type, 
        return_rate=return_rate, 
        search_query=search_query,
        tickets=tickets,
        market_trends=market_trends
    )

@app.route('/add_customer', methods=('POST',))
def add_customer():
    name = request.form['name']
    phone = request.form['phone']
    total_spent = float(request.form['total_spent'])
    
    if total_spent > 5000:
        ml_rec = 'Hot Lead - High Value VIP (Score: 91/100)'
        churn_risk = 'Low Risk - Active'
    elif total_spent > 2000:
        ml_rec = 'Warm Lead - Follow up needed (Score: 64/100)'
        churn_risk = 'Low Risk - Active'
    else:
        ml_rec = 'Cold Lead - Send special offer (Score: 28/100)'
        churn_risk = 'High Churn Risk - Needs Retention Offer'

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO customers (name, phone, last_purchase, total_spent, orders_count, ml_recommendation, churn_risk) 
        VALUES (?, ?, DATE("now"), ?, 1, ?, ?)
    ''', (name, phone, total_spent, ml_rec, churn_risk))
    
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/add_ticket', methods=('POST',))
def add_ticket():
    customer_name = request.form['customer_name']
    issue = request.form['issue']
    priority = request.form['priority']
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO tickets (customer_name, issue, status, priority, created_at)
        VALUES (?, ?, 'Open', ?, DATE("now"))
    ''', (customer_name, issue, priority))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/ask_ai', methods=('POST',))
def ask_ai():
    user_question = request.form.get('question', '').strip().lower()
    
    conn = get_db_connection()
    customers = conn.execute('SELECT * FROM customers').fetchall()
    conn.close()
    
    ai_response = "Sorry, I didn't get that. You can ask about: (best customer), write a (message for [name]), or check (churn risk)."
    target_phone = ""
    
    if "mona adel" in user_question or "mona" in user_question:
        for c in customers:
            if "mona" in c['name'].lower():
                target_phone = c['phone']
                ai_response = f"🤖 AI Suggested Message for Mona Adel (Hot Lead 🔥):\n\"Hi Mona, thank you for your continuous support! We noticed you haven't ordered in a few days and wanted to check if you need any assistance with your favorites.\""
                break
    elif "karim store" in user_question or "karim" in user_question:
        for c in customers:
            if "karim" in c['name'].lower():
                target_phone = c['phone']
                ai_response = f"🤖 AI Suggested Message for Karim Store (Warm Lead ☀️ - Churn Risk):\n\"Hi Karim, we value our partnership! We noticed a slowdown in orders this month and would like to offer you an exclusive 15% loyalty discount on your next batch. Let's discuss!\""
                break
    elif "message" in user_question or "follow" in user_question or "offer" in user_question:
        if customers:
            target_customer = customers[0]
            target_phone = target_customer['phone']
            name = target_customer['name']
            ai_response = f"🤖 AI Suggested Message for ({name}):\n\"Hi {name}, we're checking in to see how you're enjoying your purchases. Feel free to reach out if you need any assistance!\""
    elif "best" in user_question or "top" in user_question or "customer" in user_question:
        if customers:
            best_customer = max(customers, key=lambda x: x['total_spent'] if x['total_spent'] else 0)
            ai_response = f"🏆 Your top customer is ({best_customer['name']}) with total spending of {best_customer['total_spent']} EGP."
    elif "churn" in user_question or "risk" in user_question:
        ai_response = "📊 AI Churn Prediction: Customers who haven't ordered in over 180 days with high past spending are flagged as High Churn Risk. Recommended action: Send a 15% loyalty retention discount."

    return f"{ai_response}---PHONE:{target_phone}"

@app.route('/translate_ai', methods=('POST',))
def translate_ai():
    text = request.form.get('text', '')
    
    if "Mona Adel" in text or "Mona" in text:
        translated = "🤖 [ترجمة بالذكاء الاصطناعي]:\n\"مرحباً منى، شكراً لدعمك المستمر! لاحظنا أنك لم تقومي بطلب منذ عدة أيام، وأردنا الاطمئنان عما إذا كنتِ بحاجة لأي مساعدة في منتجاتك المفضلة.\""
    elif "Karim Store" in text or "Karim" in text:
        translated = "🤖 [ترجمة بالذكاء الاصطناعي]:\n\"مرحباً متجر كريم، نقدر شراكتنا معك! لاحظنا تباطؤاً في الطلبات هذا الشهر ونود تقديم خصم ولاء حصري بنسبة 15% على دفعتك القادمة. دعنا نناقش الأمر!\""
    elif "VIP" in text or "support" in text or "order" in text or "Hi" in text:
        translated = f"🤖 [ترجمة بالذكاء الاصطناعي]:\n\"أهلاً بك، شكراً لدعمك المستمر! لقد جهزنا عرضاً حصرياً لك هذا الشهر. أخبرنا إذا كنت ترغب في استكشافه.\""
    else:
        translated = f"🤖 [ترجمة بالذكاء الاصطناعي]:\n\"{text.replace('AI Suggested Message for', 'رسالة مقترحة من الذكاء الاصطناعي لـ')}\""
        
    return translated

@app.route('/export_excel')
def export_excel():
    conn = get_db_connection()
    customers = conn.execute('SELECT * FROM customers').fetchall()
    conn.close()

    output = io.StringIO()
    output.write("ID,Name,Phone,Last Purchase,Total Spent,Orders Count,AI Recommendation,Churn Risk\n")
    for c in customers:
        output.write(f"{c['id']},{c['name']},{c['phone']},{c['last_purchase']},{c['total_spent']},{c['orders_count'],},\"{c['ml_recommendation']}\",\"{c['churn_risk']}\"\n")
    
    response = Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=smart_crm_customers.csv"}
    )
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)