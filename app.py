from flask import Flask, render_template, request, redirect, url_for
from mongita import MongitaClientDisk
import os

app = Flask(__name__)

# ------------------------------------------
# Mongita Setup (local embedded NoSQL DB)
# ------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
client = MongitaClientDisk(os.path.join(BASE_DIR, "mongita_data"))

db = client.bookstore
categories_col = db.category
books_col = db.books


# ------------------------------------------
# Helper Functions
# ------------------------------------------
def get_categories():
    categories = list(categories_col.find())
    return sorted(categories, key=lambda c: c["categoryName"])


def get_next_book_id():
    books = list(books_col.find())

    if not books:
        return 1

    return max(book["bookId"] for book in books) + 1


# ------------------------------------------
# HOME PAGE
# ------------------------------------------
@app.route("/", methods=["GET"])
def home():
    categories = get_categories()
    return render_template("index.html", categories=categories)


# ------------------------------------------
# CATEGORY PAGE
# /category?categoryId=1
# ------------------------------------------
@app.route("/category", methods=["GET"])
def category():
    category_id = request.args.get("categoryId", type=int)

    categories = get_categories()
    selected_category = categories_col.find_one({"categoryId": category_id})

    books = list(books_col.find({"categoryId": category_id}))
    books = sorted(books, key=lambda b: b["title"])

    return render_template(
        "category.html",
        categories=categories,
        selectedCategory=selected_category,
        books=books,
        searchTerm=None,
        nothingFound=False
    )


# ------------------------------------------
# SEARCH
# ------------------------------------------
@app.route("/search", methods=["POST"])
def search():
    term = request.form.get("search", "").strip()

    categories = get_categories()
    all_books = list(books_col.find())

    books = [
        book for book in all_books
        if term.lower() in book["title"].lower()
    ]
    books = sorted(books, key=lambda b: b["title"])

    return render_template(
        "category.html",
        categories=categories,
        selectedCategory=None,
        books=books,
        searchTerm=term,
        nothingFound=(len(books) == 0)
    )

@app.route("/search_author", methods=["POST"])
def search_author():
    author = request.form.get("author", "").strip()

    categories = get_categories()
    all_books = list(books_col.find())

    books = [
        book for book in all_books
        if author.lower() in book["author"].lower()
    ]

    books = sorted(books, key=lambda b: b["author"])

    return render_template(
        "category.html",
        categories=categories,
        selectedCategory=None,
        books=books,
        searchTerm=author,
        nothingFound=(len(books) == 0)
    )


# ------------------------------------------
# BOOK DETAIL PAGE
# /book?bookId=3
# ------------------------------------------
@app.route("/book", methods=["GET"])
def book_detail():
    book_id = request.args.get("bookId", type=int)

    categories = get_categories()
    book = books_col.find_one({"bookId": book_id})

    if not book:
        return render_template("error.html", error="Book not found"), 404

    return render_template(
        "book_detail.html",
        book=book,
        categories=categories
    )


# ------------------------------------------
# ADD BOOK
# ------------------------------------------
@app.route("/read")
def read():
    categories = get_categories()
    books = list(books_col.find())
    books = sorted(books, key=lambda b: b["title"])

    return render_template("read.html", categories=categories, books=books)

@app.route("/create")
def create():
    categories = get_categories()
    return render_template("create.html", categories=categories)

@app.route("/create_post", methods=["POST"])
def create_post():
    categories = get_categories()
    category_id = request.form.get("categoryId", type=int)

    selected_category = next(
        (c for c in categories if c["categoryId"] == category_id),
        None
    )

    new_book = {
        "bookId": get_next_book_id(),
        "categoryId": category_id,
        "categoryName": selected_category["categoryName"] if selected_category else "",
        "title": request.form.get("title"),
        "author": request.form.get("author"),
        "isbn": request.form.get("isbn"),
        "price": request.form.get("price", type=float),
        "image": request.form.get("image"),
        "readNow": request.form.get("readNow", type=int)
    }

    books_col.insert_one(new_book)
    return redirect(url_for("read"))

@app.route("/edit/<int:id>")
def edit(id):
    categories = get_categories()
    book = books_col.find_one({"bookId": id})

    if not book:
        return render_template("error.html", error="Book not found"), 404

    return render_template("edit.html", categories=categories, book=book)

@app.route("/edit_post/<int:id>", methods=["POST"])
def edit_post(id):
    categories = get_categories()
    category_id = request.form.get("categoryId", type=int)

    selected_category = next(
        (c for c in categories if c["categoryId"] == category_id),
        None
    )

    books_col.update_one(
        {"bookId": id},
        {"$set": {
            "categoryId": category_id,
            "categoryName": selected_category["categoryName"] if selected_category else "",
            "title": request.form.get("title"),
            "author": request.form.get("author"),
            "isbn": request.form.get("isbn"),
            "price": request.form.get("price", type=float),
            "image": request.form.get("image"),
            "readNow": request.form.get("readNow", type=int)
        }}
    )

    return redirect(url_for("read"))

@app.route("/delete/<int:id>")
def delete(id):
    books_col.delete_one({"bookId": id})
    return redirect(url_for("read"))


# ------------------------------------------
# ERRORS
# ------------------------------------------

@app.errorhandler(Exception)
def handle_error(e):
    return render_template("error.html", error=e), 500


# ------------------------------------------
# RUN APP
# ------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
