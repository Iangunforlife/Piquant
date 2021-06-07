from flask import Flask, render_template
app = Flask(__name__)


@app.route('/')
def home():
    return render_template("home.html")


@app.route('/piquant/error')
def error():
    return render_template("error.html")


if __name__ == '__main__':
    app.run()
