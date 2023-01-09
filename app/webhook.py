from flask import Flask, request

app = Flask(__name__)

@app.route('/webhooks/topic/basicmessages/', methods=['POST'])
def webhook():
    # Process the webhook request
    data = request.get_json()
    print(data)
    return "OK"

if __name__ == '__main__':
    app.run(host='localhost', port=10000)