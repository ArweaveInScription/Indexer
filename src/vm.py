import json
from decimal import Decimal

from config import SNAPSHOT
from const import *
from errors import *
from verify import *
from redis_db import db_conn, get_balance_key
from sql_db import Block
from log import log
import merkle

# tokens: {tick: {tick: tick, maxSupply: maxSupply, mintLimit: mintLimit, mintBurn: mintBurn, deployTx: deployTx, deployBy: deployBy, minted: minted}}}
# balances: {tick: {user: balance}}
# executed: {everhash: error or 'ok'};
class VM:
    def __init__(self, tokens={},  balances={}, executed={}, executed_order=[], latest_tx='', count=0, log=log):
        self.tokens = tokens
        self.balances = balances
        
        self.executed = executed
        self.executed_order = executed_order
        self.latest_tx = latest_tx
        self.count = count

        self.log = log

        self.state_root = ''

    def batch_execute(self, ever_txs):
        pipe = db_conn.pipeline()

        for tx in ever_txs:
            error = self.execute(tx, pipe)
            log.info('execute tx: %s, error: %s' % (tx.everhash, error))
            self.count += 1

            # block    
            if self.count > 0 and self.count % 1000 == 0:          
                height = self.count // 1000
                
                txs = self.executed_order[(height-1)*1000:height*1000]
                executed = {}
                for tx in txs:
                    executed[tx] = self.executed[tx]

                txs_root = merkle.get_txs_root(txs, executed)
                state_root = merkle.get_state_root(self.tokens, self.balances)
                Block.create(height=height, lastest_tx=self.latest_tx, txs_root=txs_root, state_root=state_root)

                snapshot = {
                    'block': height,
                    'state_root': state_root,
                    'txs_root': txs_root,  
                    'tokens': self.tokens,
                    'balances': self.balances,
                    'executed_order': txs,
                    'executed': executed,
                    'latest_tx': self.latest_tx,
                    'count':self.count
                }
                json.dump(snapshot, open(f'{SNAPSHOT}/{height}.json', 'w'), indent=4)
                
                log.info('create block: %s; save snapshot' % height)
                
        pipe.execute()
        return ever_txs
    
    def execute(self, ever_tx, pipe=None):
        if ever_tx.everhash in self.executed:
            return ERR_TX_EXECUTED

        error = self.__execute(ever_tx, pipe)
        self.latest_tx = ever_tx.everhash
        self.executed_order.append(ever_tx.everhash)
        if not error:
            self.executed[ever_tx.everhash] = 'ok'
            ever_tx.prc20_status = 'ok'
        else:
            self.executed[ever_tx.everhash] = error
            ever_tx.prc20_status = error
        
        # into db
        if pipe:
            pipe.hset('executed', ever_tx.everhash, self.executed[ever_tx.everhash])
            pipe.lpush('executed_order', ever_tx.everhash)
            pipe.set('latest_tx', self.latest_tx)

        return error
    
    # return error message if failed
    def __execute(self, ever_tx, pipe):
        try:
            params = json.loads(ever_tx.data)
        except:
            return ERR_INVALID_EVER_TX_DATA
        
        if ever_tx.tx_to != BURN_ADDRESS:
            return ERR_INVALID_TX_To
        if params.get('p') != PROTOCOL:
            return ERR_INVALID_PROTOCOL  
        if not params.get('op'):
            return ERR_INVALID_OP
        if not verify_tick(params.get('tick', '')):
            return ERR_INVALID_TICK
        params['tick'] = params['tick'].lower()

        op = params['op']
        ever_tx.op = op
        ever_tx.tick = params['tick']
        if op == OP_DEPLOY:
            return self.__execute_deploy(params, ever_tx, pipe)
        if op == OP_MINT:
            return self.__execute_mint(params, ever_tx, pipe)
        if op == OP_TRANSFER:
            return self.__execute_transfer(params, ever_tx, pipe)
        return ERR_INVALID_OP
    
    def __execute_deploy(self, params, ever_tx, pipe):
        tick = params['tick']
        if self.tokens.get(tick):
            return ERR_TICK_EXISTS
        max_supply = params.get('max')
        if not is_digit_string(max_supply):
            return ERR_INVALID_MAX_SUPPLY
        ever_tx.max_supply = max_supply
        max_supply = int(max_supply)
        if max_supply <= 0 or max_supply > UINT64_MAX:
            return ERR_INVALID_MAX_SUPPLY
        
        mint_limit = params.get('lim')
        if mint_limit:
            if not is_digit_string(mint_limit):
                return ERR_INVALID_MINT_LIMIT
            mint_limit = int(mint_limit)
            if mint_limit <= 0 or mint_limit > max_supply:
                return ERR_INVALID_MINT_LIMIT
        else:
            mint_limit = max_supply
        ever_tx.mint_limit = str(mint_limit)
        
        mint_burn = params.get('burn')
        if not mint_burn:
            return ERR_INVALID_MINT_BURN
        
        if not is_string(mint_burn):
            return ERR_INVALID_MINT_BURN
        if mint_burn.find('.') != -1 and len(mint_burn.split('.')[-1]) > MINT_TOKEN_DECIMALS:
            return ERR_INVALID_MINT_BURN
        try:
            mint_burn = Decimal(mint_burn)
        except:
            return ERR_INVALID_MINT_BURN
        if mint_burn < Decimal(MIN_MINT_BURN):
            return ERR_INVALID_MINT_BURN
        mint_burn = int(mint_burn * 10**BURN_TOKEN_DECIMALS)
        ever_tx.mint_burn = str(mint_burn)
        
        if ever_tx.token_id != BURN_TOKEN:
            return ERR_INVALID_DEPLOY_TOKEN 
        if ever_tx.amount != DEPLOY_BURN:
            return ERR_INVALID_DEPLOY_BURN

        token = {
            'tick': tick,
            'maxSupply': max_supply,
            'mintLimit': mint_limit,
            'mintBurn': mint_burn,
            'deployTx': ever_tx.everhash,
            'deployBy': ever_tx.tx_from,
            'minted': 0
        }
        self.tokens[tick] = token
        
        if pipe:
            pipe.hset('tokens', tick, json.dumps(token))
        
        return None
    
    def __execute_mint(self, params, ever_tx, pipe):
        tick = params['tick']
        if not self.tokens.get(tick):
            return ERR_TICK_NOT_EXISTS
        token = self.tokens[tick]

        if token['minted'] >= token['maxSupply']:
            return ERR_TOKEN_ALREADY_MINTED
        
        amount = params.get('amt')
        if not is_digit_string(amount):
            return ERR_INVALID_MINT_AMOUNT
        amount = int(amount)
        if amount <= 0 or amount > UINT64_MAX:
            return ERR_INVALID_MINT_AMOUNT
        if amount > token['mintLimit']:
            return ERR_INVALID_MINT_AMOUNT
        
        if amount + token['minted'] > token['maxSupply']:
            amount = token['maxSupply'] - token['minted']
        ever_tx.amt = str(amount)

        if ever_tx.token_id != MINT_TOKEN:
            return ERR_INVALID_MINT_TOKEN
        
        if not is_digit_string(ever_tx.amount):
            return ERR_INVALID_MINT_BURN
        ever_tx_amount = int(ever_tx.amount)
        if ever_tx_amount != token['mintBurn']:
            return ERR_INVALID_MINT_BURN
       
        user = ever_tx.tx_from
        if not self.balances.get(tick):
            self.balances[tick] = {}

        if not self.balances[tick].get(user):
            self.balances[tick][user] = amount
        else:
            self.balances[tick][user] += amount
        
        token['minted'] += amount

        if pipe:
            pipe.hset('tokens', tick, json.dumps(token))
            key = get_balance_key(tick)
            pipe.hset(key, user, self.balances[tick][user])

        return None
    
    def __execute_transfer(self, params, ever_tx, pipe):
        tick = params['tick']
        if not self.tokens.get(tick):
            return ERR_TICK_NOT_EXISTS

        # no check if address is valid
        to = params.get('to')
        if to == '' or not is_string(to):
            return ERR_INVALID_TO
        to = verify_address(to)
        ever_tx.to = to

        amount = params.get('amt')
        if not is_digit_string(amount):
            return ERR_INVALID_TRANSFER_AMOUNT
        amount = int(amount)
        if amount <= 0 or amount > UINT64_MAX:
            return ERR_INVALID_TRANSFER_AMOUNT
        ever_tx.amt = str(amount)
        
        user = ever_tx.tx_from
        if not self.balances.get(tick):
            return ERR_INSUFFICIENT_BALANCE
        if not self.balances[tick].get(user):
            return ERR_INSUFFICIENT_BALANCE
        if self.balances[tick][user] < amount:
            return ERR_INSUFFICIENT_BALANCE
        
        self.balances[tick][user] -= amount
        if self.balances[tick][user] == 0:
            del self.balances[tick][user]

        if not self.balances[tick].get(to):
            self.balances[tick][to] = 0
        self.balances[tick][to] += amount

        # db
        if pipe:
            key = get_balance_key(tick)
            if not self.balances[tick].get(user):
                pipe.hdel(key, user)
            else:
                pipe.hset(key, user, self.balances[tick][user])
            pipe.hset(key, to, self.balances[tick][to])

        return None