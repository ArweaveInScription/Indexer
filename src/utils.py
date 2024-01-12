import time
from log import log

def get_new_txs_from_everpay(client, address, start_cursor, token_tag='', action='', without_action='', sleep_time=0.2, max_txs=200):
    result = []
    has_next_page = True
    limit = 100

    while True:

        if not has_next_page:
            return result, start_cursor
        
        if len(result) >= max_txs:
            return result, start_cursor
        
        try:
            data = client.get_txs(address, order_by='asc', start_cursor=start_cursor, 
                                  limit=limit, action=action, 
                                  without_action=without_action, 
                                  token_tag=token_tag)
        except Exception as e:
            log.warn('failed to fetch new txs from everpay api server:', e)
            time.sleep(sleep_time * 5)
            continue
        
        if (not data.get('txs')) or len(data['txs']) == 0:
            return result, start_cursor

        has_next_page = data['hasNextPage']

        txs = data['txs']
        #print('fetched', len(txs), 'txs from everpay api server')
        result.extend(txs)
        start_cursor = txs[-1]['rawId']
        
        time.sleep(sleep_time)