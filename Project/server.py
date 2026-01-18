from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    # Instead of returning a string, we return the HTML file
    return render_template("home_page.html")

@app.route("/learning")
def learning_page():
    return render_template("learning.html")

if __name__ == "__main__":
    app.run(debug=True)