from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"  # ログイン保持に必要

def get_db():
    conn = sqlite3.connect("stock.db")
    conn.row_factory = sqlite3.Row
    return conn

# 商品一覧
@app.route("/")
def index():
    conn = get_db()
    items = conn.execute("""
    SELECT 
        Item.*,
        COALESCE(SUM(
            CASE 
                WHEN StockTransaction.transaction_type='IN' 
                THEN StockTransaction.quantity
                WHEN StockTransaction.transaction_type='OUT' 
                THEN -StockTransaction.quantity
            END
        ),0) AS stock
    FROM Item
    LEFT JOIN StockTransaction 
        ON Item.id = StockTransaction.item_id
    WHERE Item.deleted=0
    GROUP BY Item.id
    """).fetchall()

    conn.close()
    return render_template("index.html", items=items)

# 商品登録
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        name = request.form["name"]
        category = request.form["category"]
        origin = request.form["origin"]
        reorder_level = request.form["reorder_level"]
        unit = request.form["unit"]

        conn = get_db()
        conn.execute("""
            INSERT INTO Item (name, category, origin, reorder_level, unit)
            VALUES (?, ?, ?, ?, ?)
        """, (name, category, origin, reorder_level, unit))
        conn.commit()
        conn.close()

        return redirect("/stock_in")

    return render_template("add.html")

# 商品編集
@app.route("/edit/<int:item_id>", methods=["GET", "POST"])
def edit(item_id):
    conn = get_db()

    if request.method == "POST":
        name = request.form["name"]
        category = request.form["category"]
        origin = request.form["origin"]
        reorder_level = request.form["reorder_level"]
        unit = request.form["unit"]

        conn.execute("""
            UPDATE Item
            SET name=?, category=?, origin=?, reorder_level=?, unit=?
            WHERE id=?
        """, (name, category, origin, reorder_level, unit, item_id))
        conn.commit()
        conn.close()

        return redirect("/")

    item = conn.execute(
        "SELECT * FROM Item WHERE id=?",
        (item_id,)
    ).fetchone()
    conn.close()

    return render_template("edit.html", item=item)

@app.route("/delete/<int:item_id>")
def delete(item_id):
    conn = get_db()
    conn.execute(
        "UPDATE Item SET deleted=1 WHERE id=?",
        (item_id,)
    )
    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        staff_id = request.form["staff_id"]
        session["staff_id"] = staff_id
        return redirect("/")  # トップへ戻る
    return render_template("login.html")

@app.route("/history")
def history():
    conn = sqlite3.connect("stock.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            StockTransaction.*,
            Item.name AS item_name
        FROM StockTransaction
        JOIN Item ON StockTransaction.item_id = Item.id
        ORDER BY transaction_date DESC
    """)

    data = cur.fetchall()
    conn.close()

    return render_template("history.html", data=data)

# 在庫追加
@app.route("/stock_in/<int:item_id>", methods=["POST"])
def stock_in_from_index(item_id):
    conn = get_db()
    qty = request.form["qty"]

    conn.execute("""
        INSERT INTO StockTransaction
        (item_id, transaction_type, quantity, transaction_date)
        VALUES (?, 'IN', ?, DATETIME('now','localtime'))
    """, (item_id, qty))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/stock_out/<int:item_id>", methods=["POST"])
def stock_out_from_index(item_id):
    conn = get_db()
    qty = request.form["qty"]

    conn.execute("""
        INSERT INTO StockTransaction
        (item_id, transaction_type, quantity, transaction_date)
        VALUES (?, 'OUT', ?, DATETIME('now','localtime'))
    """, (item_id, qty))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/deleted_items")
def deleted_items():
    conn = get_db()
    items = conn.execute(
        "SELECT * FROM Item WHERE deleted=1"
    ).fetchall()
    conn.close()

    return render_template("deleted_items.html", items=items)

if __name__ == "__main__":
    app.run()
