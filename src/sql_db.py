import datetime
from peewee import Model, CharField, DateTimeField, SqliteDatabase, IntegerField
from config import DB

db = SqliteDatabase(DB)

class Tx(Model):
    created_at = DateTimeField(default=datetime.datetime.now)

    # everpay tx
    everhash = CharField(unique=True, index=True)
    token_symbol = CharField(null=False)
    token_id = CharField(null=False)
    action = CharField(null=False)
    tx_from = CharField(null=False)
    nonce = CharField(null=False)
    tx_to = CharField(null=False)
    amount = CharField(null=False)
    data = CharField(null=False)
    internal_status = CharField(null=False)
    chain_type = CharField(null=False)
    chain_id = CharField(null=False)

    # prc-20 tx
    op = CharField(null=True)
    tick = CharField(null=True)
    max_supply = CharField(null=True)
    mint_limit = CharField(null=True)
    mint_burn = CharField(null=True)
    amt = CharField(null=True)
    to = CharField(null=True)
    
    prc20_status = CharField(null=True)

    class Meta:
        database = db

class Block(Model):
    created_at = DateTimeField(default=datetime.datetime.now)

    height = IntegerField(unique=True, index=True)
    lastest_tx = CharField(null=False)
    txs_root = CharField(null=False)
    state_root = CharField(null=False)

    class Meta:
        database = db

def get_tx_dict(tx):
   return {
        'everhash': tx.everhash,
        'token_symbol': tx.token_symbol,
        'token_id': tx.token_id,
        'action': tx.action,
        'tx_from': tx.tx_from,
        'nonce': tx.nonce,
        'tx_to': tx.tx_to,
        'amount': tx.amount,
        'data': tx.data,
        'internal_status': tx.internal_status,
        'chain_type': tx.chain_type,
        'chain_id': tx.chain_id,
        'op': tx.op,
        'tick': tx.tick,
        'max_supply': tx.max_supply,
        'mint_limit': tx.mint_limit,
        'mint_burn': tx.mint_burn,
        'amt': tx.amt,
        'to': tx.to,
        'prc20_status': tx.prc20_status,
    }

db.connect()
db.create_tables([Tx, Block])