import os

access_key = raw_input("Access key: ")
secret_key = raw_input("Secret key: ")

if os.path.isfile('keys'):
    os.rename('keys', 'keys.old')
with open('keys', 'w') as f:
    f.write(':'.join([access_key, secret_key]))
if os.path.isfile('keys.old'):
    os.remove('keys.old')