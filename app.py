from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3, datetime, xml.etree.ElementTree as ET
import os

app = Flask(__name__)
app.secret_key = "123"

# ---------------- BANCO ----------------
def db():
    return sqlite3.connect("banco.db")

def criar():
    conn = db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS produtos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        categoria TEXT,
        preco REAL,
        estoque INTEGER
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS vendas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto TEXT,
        valor REAL,
        data TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS pedidos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT,
        produto TEXT,
        valor REAL,
        status TEXT
    )""")

    conn.commit()
    conn.close()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["user"] == "admin" and request.form["pass"] == "123":
            session["logado"] = True
            return redirect(url_for("home"))
    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- HOME ----------------
@app.route("/home")
def home():
    if not session.get("logado"):
        return redirect(url_for("login"))
    return render_template("home.html")

# ---------------- PRODUTOS ----------------
@app.route("/produtos", methods=["GET","POST"])
def produtos():
    if not session.get("logado"):
        return redirect(url_for("login"))

    conn = db()
    c = conn.cursor()

    if request.method == "POST":
        c.execute("""INSERT INTO produtos(nome,categoria,preco,estoque)
                     VALUES (?,?,?,?)""",
        (request.form["nome"],
         request.form["categoria"],
         float(request.form["preco"]),
         int(request.form["estoque"])))
        conn.commit()

    c.execute("SELECT * FROM produtos")
    dados = c.fetchall()
    conn.close()

    return render_template("produtos.html", produtos=dados)

# ---------------- PDV ----------------
@app.route("/pdv", methods=["GET","POST"])
def pdv():
    if not session.get("logado"):
        return redirect(url_for("login"))

    conn = db()
    c = conn.cursor()

    if request.method == "POST":
        nome = request.form["produto"]
        valor = float(request.form["valor"])

        c.execute("INSERT INTO vendas(produto,valor,data) VALUES (?,?,?)",
                  (nome, valor, str(datetime.date.today())))

        c.execute("UPDATE produtos SET estoque = estoque - 1 WHERE nome=?", (nome,))
        conn.commit()

    c.execute("SELECT * FROM produtos")
    produtos = c.fetchall()
    conn.close()

    return render_template("pdv.html", produtos=produtos)

# ---------------- DELIVERY ----------------
@app.route("/delivery", methods=["GET","POST"])
def delivery():
    if not session.get("logado"):
        return redirect(url_for("login"))

    conn = db()
    c = conn.cursor()

    if request.method == "POST":
        c.execute("""INSERT INTO pedidos(cliente,produto,valor,status)
                     VALUES (?,?,?,?)""",
        (request.form["cliente"],
         request.form["produto"],
         float(request.form["valor"]),
         "Em preparo"))
        conn.commit()

    c.execute("SELECT * FROM pedidos")
    pedidos = c.fetchall()
    conn.close()

    return render_template("delivery.html", pedidos=pedidos)

# ---------------- IMPORTAR XML ----------------
@app.route("/importar_xml", methods=["GET","POST"])
def importar_xml():
    if not session.get("logado"):
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            caminho = "xml/nota.xml"

            if not os.path.exists(caminho):
                return "Arquivo XML não encontrado!"

            tree = ET.parse(caminho)
            root = tree.getroot()

            conn = db()
            c = conn.cursor()

            for item in root.iter("det"):
                nome = item.find(".//xProd")
                preco = item.find(".//vProd")

                if nome is not None and preco is not None:
                    c.execute("""INSERT INTO produtos(nome,categoria,preco,estoque)
                                 VALUES (?,?,?,?)""",
                              (nome.text, "XML", float(preco.text), 1))

            conn.commit()
            conn.close()

            return "XML importado com sucesso!"

        except Exception as e:
            return f"Erro ao importar XML: {e}"

    return render_template("importar_xml.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if not session.get("logado"):
        return redirect(url_for("login"))

    conn = db()
    c = conn.cursor()

    c.execute("SELECT SUM(valor) FROM vendas")
    total = c.fetchone()[0] or 0

    conn.close()
    return render_template("dashboard.html", total=total)

# ---------------- INICIAR ----------------
criar()

if __name__ == "__main__":
    app.run(debug=True)