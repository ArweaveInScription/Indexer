import json
from flask import Flask, jsonify
from flask_cors import CORS

from redis_db import get_token, get_balance, get_tx, get_state_from_db
from sql_db import Block
from verify import verify_address
from merkle import get_state_root
from config import DEBUG
app = Flask(__name__)
CORS(app)

@app.route('/token/<tick>', methods=['GET'])
def token(tick):
    data = get_token(tick)
    if data:
        data = json.loads(data)
    return jsonify(data)

@app.route('/balance/<tick>/<user>', methods=['GET'])
def balance(tick, user):
    user = verify_address(user)
    data = get_balance(tick, user)
    if not data:
        data = 0
    return jsonify({
        'tick': tick,
        'user': user,
        'balance': int(data)
    })

@app.route('/tx/<everhash>', methods=['GET'])
def tx(everhash):
    data = get_tx(everhash)
    return str(data)

@app.route('/block/<height>', methods=['GET'])
def block(height):
    b = Block.get(height=height)
    if not b:
        return jsonify(None)
    
    return jsonify({
        'height': b.height,
        'lastest_tx': b.lastest_tx,
        'txs_root': b.txs_root,
        'state_root': b.state_root
    })

@app.route('/info', methods=['GET'])
def info():
    data = get_state_from_db(verbose=False)
    data['latestTx'] = data['latest_tx']
    data['stateRoot'] = get_state_root(data['tokens'], data['balances'])
    return jsonify(data)

if __name__ == '__main__':
    if DEBUG:
        app.run(host='0.0.0.0', port=5000, debug=True)    
    else:
	    app.run()
