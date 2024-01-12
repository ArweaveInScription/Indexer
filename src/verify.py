from const import *
from web3.auto import w3

def is_string(v):
    return isinstance(v, str)

def is_digit_string(v):
    return is_string(v) and v.isdigit()

def verify_tick(tick):
    if not is_string(tick):
        return False
    if len(tick.encode('u8')) != TICK_NAME_LENGTH:
        return False
    return True

# return checksum address if eth else return ''
def verify_eth_address(addr):
    try:
        return w3.to_checksum_address(addr)
    except:
        return ''

def verify_address(addr):
    if verify_eth_address(addr) != '':
        return verify_eth_address(addr)
    return addr