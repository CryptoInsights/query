import pymongo

from config import config

client = pymongo.MongoClient(config.mongo_url,
                             ssl=True,
                             ssl_ca_certs=config.ssl_ca_cert,
                             ssl_certfile=config.ssl_cert,
                             ssl_keyfile=config.ssl_key,
                             ssl_match_hostname=False)

db = client.ingest
