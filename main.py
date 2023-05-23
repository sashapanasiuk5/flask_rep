from flask import Flask, jsonify
import os
import file

app = Flask(__name__)


@app.route('/')
def index():
    os.system('python test.py')

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
