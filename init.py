from flask import Flask, render_template, request, redirect, url_for
from forms import *
import shelve, User, referalcode
app = Flask(__name__)


@app.route('/')
def home():
    return render_template("home.html")


@app.route('/piquant/error')
def error():
    return render_template("error.html")


@app.route('/audit')
def audit():
    return render_template('Includes/audit.html')


if __name__ == '__main__':
    app.run()
