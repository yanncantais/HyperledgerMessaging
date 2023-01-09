from flask import Flask, request
import sys


port = sys.argv[1]


app_flask = Flask(__name__)

@app_flask.route('/webhooks/topic/basicmessages/', methods=['POST'])
def webhook():
    # Process the webhook request
    data = request.get_json()
    print(data)
    return "OK"

if __name__ == '__main__':
    app_flask.run(host='localhost', port=port)