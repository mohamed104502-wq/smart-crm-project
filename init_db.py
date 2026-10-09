import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def init_db():
    print("جاري قراءة ملف Superstore.xlsx وتجهيز قاعدة البيانات الشاملة...")
    
    excel_path = 'Superstore.xlsx'
    df = pd.read_excel(excel_path, sheet_name='Orders')
    
    customer_summary = df.groupby(['Customer ID', 'Customer Name']).agg(
        phone=('Postal Code', lambda x: '01' + str(abs(hash(str(x.iloc[0]))) % 1000000000)),
        last_purchase=('Order Date', 'max'),
        total_spent=('Sales', 'sum'),
        orders_count=('Order ID', 'count')
    ).reset_index()
    
    conn = sqlite3.connect('crm_database.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            last_purchase TEXT,
            total_spent REAL,
            orders_count INTEGER,
            ml_recommendation TEXT,
            churn_risk TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            issue TEXT NOT NULL,
            status TEXT NOT NULL,
            priority TEXT NOT NULL,
            created_at TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_category TEXT NOT NULL,
            trend_change TEXT NOT NULL,
            recommendation TEXT NOT NULL
        )
    ''')

    cursor.execute("DELETE FROM customers")
    cursor.execute("DELETE FROM tickets")
    cursor.execute("DELETE FROM market_trends")

    current_date = pd.to_datetime(df['Order Date']).max()
    
    for index, row in customer_summary.iterrows():
        name = row['Customer Name']
        phone = row['phone']
        last_purchase_dt = pd.to_datetime(row['last_purchase'])
        last_purchase = str(last_purchase_dt)[:10]
        total_spent = float(row['total_spent'])
        orders_count = int(row['orders_count'])
        
        if total_spent > 5000:
            ml_rec = 'Hot Lead - High Value VIP (Score: 91/100)'
        elif total_spent > 2000:
            ml_rec = 'Warm Lead - Follow up needed (Score: 64/100)'
        else:
            ml_rec = 'Cold Lead - Send special offer (Score: 28/100)'
            
        days_inactive = (current_date - last_purchase_dt).days
        if days_inactive > 180 and total_spent > 1500:
            churn_risk = 'High Churn Risk - Needs Retention Offer (15% Discount)'
        else:
            churn_risk = 'Low Risk - Active'

        cursor.execute('''
            INSERT INTO customers (name, phone, last_purchase, total_spent, orders_count, ml_recommendation, churn_risk) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, phone, last_purchase, total_spent, orders_count, ml_rec, churn_risk))

    sample_tickets = [
        ('Mona Adel', 'Delayed shipping on order #1042', 'Open', 'High', '2026-09-25'),
        ('Karim Store', 'Damaged product received in last batch', 'Pending', 'Medium', '2026-09-26'),
        ('Youssef Hany', 'Inquiry about bulk order discount', 'Resolved', 'Low', '2026-09-20')
    ]
    cursor.executemany('''
        INSERT INTO tickets (customer_name, issue, status, priority, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', sample_tickets)

    sample_trends = [
        ('Technology / Accessories', '+300% Local Search Surge', 'Restock wireless mechanical keyboards immediately based on local demand.'),
        ('Office Supplies', '+45% Demand', 'Run targeted promotions for ergonomic chairs and desk organizers.'),
        ('Furniture', 'Stable Trend', 'Maintain current stock levels; focus on bundling offers.')
    ]
    cursor.executemany('''
        INSERT INTO market_trends (product_category, trend_change, recommendation)
        VALUES (?, ?, ?)
    ''', sample_trends)

    conn.commit()
    conn.close()
    print(f"تم بنجاح إنشاء القاعدة الشاملة وتصنيف {len(customer_summary)} عميل!")

if __name__ == '__main__':
    init_db()