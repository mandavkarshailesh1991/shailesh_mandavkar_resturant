from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import qrcode
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Ensure 'static' directory exists
if not os.path.exists("static"):
    os.makedirs("static")

# Serve static HTML files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Database setup
conn = sqlite3.connect("restaurant.db", check_same_thread=False)
cursor = conn.cursor()

# Create tables
cursor.execute("DROP TABLE IF EXISTS menu")  # This will remove old table

cursor.execute('''CREATE TABLE IF NOT EXISTS menu (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT UNIQUE, 
                    price REAL)''')

cursor.execute("DROP TABLE IF EXISTS orders")  # This will remove old table

cursor.execute('''
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        items TEXT NOT NULL,
        total_price REAL NOT NULL,
	order_status TEXT DEFAULT 'Pending'  -- New column
    )
''')
conn.commit()


# Clear the menu table before inserting new items
cursor.execute("DELETE FROM menu")
conn.commit()

# Reset the auto-increment ID (optional, keeps IDs clean)
cursor.execute("DELETE FROM sqlite_sequence WHERE name='menu'")
conn.commit()

# Preload sample menu items
sample_menu = [
    ("Burger", 5.99),
    ("Pizza", 8.99),
    ("Pasta", 7.49),
    ("Salad", 4.99),
    ("Sushi", 12.99),
    ("Tacos", 6.99)
]

cursor.executemany("INSERT INTO menu (name, price) VALUES (?, ?)", sample_menu)
conn.commit()

# Define models
class OrderRequest(BaseModel):
    customer_name: str
    items: list[str]

@app.get("/menu")
def get_menu():
    cursor.execute("SELECT * FROM menu")
    items = cursor.fetchall()
    return {"menu": [{"id": i[0], "name": i[1], "price": i[2]} for i in items]}

@app.post("/order")
def place_order(order: OrderRequest):
    cursor.execute("SELECT name, price FROM menu")
    menu_items = {name: price for name, price in cursor.fetchall()}
    
    selected_items = []
    total_price = 0.0
    for item in order.items:
        if item not in menu_items:
            raise HTTPException(status_code=400, detail=f"Item '{item}' not found in menu")
        selected_items.append(item)
        total_price += menu_items[item]
    
    cursor.execute("INSERT INTO orders (customer_name, items, total_price) VALUES (?, ?, ?)", 
                   (order.customer_name, ", ".join(selected_items), total_price))
    conn.commit()
    return {"message": "Order placed successfully", "customer_name": order.customer_name, "items": selected_items, "total_price": total_price}

@app.post("/orders/{order_id}/complete")
def complete_order(order_id: int):
    cursor.execute("UPDATE orders SET order_status = 'Completed' WHERE id = ?", (order_id,))
    conn.commit()
    return {"message": "Order marked as completed"}


@app.get("/orders")
def get_orders():
    cursor.execute("SELECT id, customer_name, items, total_price, order_status FROM orders")
    orders = cursor.fetchall()
    return {"orders": [{"id": row[0], "customer_name": row[1], "items": row[2], "total_price": row[3], "order_status": row[4]} for row in orders]}


@app.get("/generate_qr")
def generate_qr():
    qr = qrcode.make("http://127.0.0.1:8000/menu")
    qr.save("menu_qr.png")
    return {"message": "QR code generated", "file": "menu_qr.png"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
