import logging
import os
import sys
import gnupg  # Make sure this is python-gnupg

def detectPublicKey(key_dir):
    logging.info('Detecting public key')

    public_key_path = os.path.join(key_dir, 'public.key')

    if not os.path.isfile(public_key_path):
        logging.error(f'Public key file not found at {public_key_path}')
        sys.exit(1)

    with open(public_key_path, 'r') as key_file:
        pub_key = key_file.read()
    
    gpg = gnupg.GPG(options=['--yes', '--always-trust'])
    public_import_result = gpg.import_keys(pub_key)

    logging.info('Public key valid')

def importPrivateKey(sign_key):
    logging.info('Importing private key')

    gpg = gnupg.GPG(options=['--yes', '--always-trust'])
    private_import_result = gpg.import_keys(sign_key)

    private_key_id = private_import_result.fingerprints[0]
    logging.info('Private key valid')

    logging.info('-- Done importing key --')

    return private_key_id
