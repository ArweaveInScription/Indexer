import hashlib
from merkly.mtree import MerkleTree

def sha256(x, y):
    data = x + y
    return hashlib.sha256(data).digest()

def get_txs_root(order, txs):
    leaves = []
    for t in order:
        
        r = txs[t]
        if r == 'ok':
            r == "0"
        else:
            r = "1"

        leaves.append(f'{t}:{r}')
    
    tree = MerkleTree(leaves, sha256)
    return tree.root.hex()

def get_balances_root(balances):
    users = sorted(balances.keys())
    leaves = [f'{u}:{balances[u]}' for u in users]
    tree = MerkleTree(leaves, sha256)
    return tree.root.hex()

def get_token_root(token, balances):
    balances_root = get_balances_root(balances)
    leaves = [
        f'tick:{token["tick"]}',
        f'maxSupply:{token["maxSupply"]}',
        f'mintLimit:{token["mintLimit"]}',
        f'mintBurn:{token["mintBurn"]}',
        f'deployTx:{token["deployTx"]}',
        f'deployBy:{token["deployBy"]}',
        f'minted:{token["minted"]}',
        f'balancesRoot:{balances_root}'
    ]
    tree = MerkleTree(leaves, sha256)
    return tree.root.hex()

def get_state_root(tokens, balances):
    if len(tokens) == 1:
        t = list(tokens.keys())[0]
        token = tokens[t]
        return get_token_root(token, balances[t]) 

    ticks = sorted(tokens.keys())
    leaves = []
    for t in ticks:
        token = tokens[t]
        token_root = get_token_root(token, balances[t])
        leaves.append(f'{t}:{token_root}')
    tree = MerkleTree(leaves, sha256)
    return tree.root.hex()