import json
from redis import Redis
from config import *

db_conn = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, charset="utf-8", decode_responses=True)

def get_balance_key(tick):
    return f'{tick}_balances'

def get_token(tick):
    return db_conn.hget('tokens', tick)

def get_tokens():
    return db_conn.hgetall('tokens')

def get_balance(tick, user):
    key = get_balance_key(tick)
    return db_conn.hget(key, user)

def get_balances(tick):
    key = get_balance_key(tick)
    return db_conn.hgetall(key)

def get_executed():
    order = db_conn.lrange('executed_order', 0, -1)
    executed = db_conn.hgetall('executed')
    count = db_conn.hlen('executed')
    return order, executed, count

def get_tx(everhash):
    return db_conn.hget('executed', everhash)

def load_tokens_from_db():
    tokens = {}
    for tick, d in get_tokens().items():
        tokens[tick] = json.loads(d)
    return tokens

def get_state_from_db(verbose=True):
    latest_tx = db_conn.get('latest_tx')
    if not latest_tx:
        return None
    
    tokens = load_tokens_from_db()
    ticks = tokens.keys()
    balances = {}
    for tick in ticks:
        balances[tick] = {}
        for user, balance in get_balances(tick).items():
            balances[tick][user] = int(balance)
    
    state = state = {
        'latest_tx': latest_tx,
        'tokens': tokens,
        'balances': balances,
    }
    if not verbose:
        return state

    order, exectued, count = get_executed()

    state['execute_order'] = order
    state['executed'] = exectued
    state['count'] = count
    
    return state

def put_state_to_db(state, db_conn):
    pipe = db_conn.pipeline()
    pipe.set('latest_tx', state['latest_tx'])

    pipe.delete('tokens')
    for tick, data in state['tokens'].items():
        pipe.hset('tokens', tick, json.dumps(data))
    
    for tick, balances in state['balances'].items():
        key = get_balance_key(tick)
        pipe.delete(key)
        for u, b in balances.items():
            pipe.hset(key, u, b)

    pipe.delete('executed_order')
    for h in state['execute_order']:
        pipe.rpush('executed_order', h)
    
    pipe.delete('executed')
    for h, r in state['executed'].items():
        pipe.hset('executed', h, r)
    
    pipe.execute()