import time, os
import everpay

from vm import VM
from config import PAY, GENSIS, SNAPSHOT
from const import BURN_ADDRESS
from utils import get_new_txs_from_everpay
from redis_db import get_state_from_db
from sql_db import Tx, get_tx_dict
from log import log
from verify import verify_address

if not os.path.exists(SNAPSHOT):
    os.makedirs(SNAPSHOT)

sleep_time = 1

state = get_state_from_db()
if state:
    vm = VM(state['tokens'], state['balances'], state['executed'], state['execute_order'], state['latest_tx'], state['count'])
    latest_tx = state['latest_tx']
    log.info(f'vm initialized, sync from latest_tx {latest_tx}, count: {vm.count}')
else:
    latest_tx = GENSIS
    vm = VM()
    log.info('vm initialized, sync from gensis tx')

client = everpay.Client(PAY, timeout=2)
tx = client.get_tx(latest_tx)
cursor = tx['tx']['rawId']
log.info(f'sync from cursor: {cursor}')

while True:
    txs, cursor = get_new_txs_from_everpay(client, BURN_ADDRESS, cursor, sleep_time=sleep_time)
    log.info(f'synced {len(txs)} txs. cursor: {cursor}')

    if len(txs) == 0:
        time.sleep(sleep_time)
        continue
    
    etxs = []
    for tx in txs:
        log.info(f'new tx: {tx["rawId"]} {tx["everHash"]}')
        etx = Tx(everhash=tx['everHash'], token_symbol=tx['tokenSymbol'], 
                 token_id=tx['tokenID'], action=tx['action'], tx_from=verify_address(tx['from']), 
                 nonce=tx['nonce'], tx_to=verify_address(tx['to']), amount=tx['amount'], 
                 data=tx['data'], internal_status=tx['internalStatus'], 
                 chain_type=tx['chainType'], chain_id=tx['chainID'])
        
        etxs.append(etx)

    etxs = vm.batch_execute(etxs)
    etxs_dict = [get_tx_dict(t) for t in etxs]
    Tx.insert_many(etxs_dict).execute()