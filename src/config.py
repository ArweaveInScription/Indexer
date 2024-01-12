import os

DEBUG = False
AR = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,0x4fadc7a98f2dc96510e42dd1a74141eeae0c1543'
PAY = 'https://api.everpay.io'

GENSIS = '0x4789d5c38edaf14745bc207489da8118ba25e56b33f8be0e65ecfbb1c9f680e9'

REDIS_HOST = os.getenv('REDIS_HOST', "localhost")
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
REDIS_DB = os.getenv('REDIS_DB', 0)

DB = "indexer.db"

SNAPSHOT = "snapshot"