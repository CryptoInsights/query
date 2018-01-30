# query
A tool that consumes data from ingest server and do analyze on it.

## Run
### Prerequisites
You'll need a RSA key and corresponding certification file in order to connect to backend database.
- Create a new folder: `$ mkdir keys/mykeys`
- Generate a RSA key pair: `$ openssl genrsa -out my-name.key 2048` in folder `keys/mykeys`
- Create a CSR file from your key: `$ openssl req -new -key my-name.key -out my-name.csr`
- Send the CSR file to [danielwpz@gmail](mailto:danielwpz@gmail.com) and ask for a cert file signed by the root key.
- After you get back a cert file (`my-name.crt`), put it in `keys/mykeys`.
- Change `config/config.py` so that all the key paths are correct.

### Run
- `$ pip3 install -r requirements.txt`
- `$ jupyter notebook`
