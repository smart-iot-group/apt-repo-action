import logging
import os
import sys


def detectPublicKey(gpg, key_dir):
    logging.info('Detecting public key')

    public_key_path = os.path.join(key_dir, 'public.key')
    logging.debug('Looking for public key at {}'.format(public_key_path))

    key_exists = os.path.isfile(public_key_path)

    logging.debug('Existing public key file exists? {}'.format(key_exists))

    if not key_exists:
        logging.error('Public key file not found at {}'.format(public_key_path))
        sys.exit(1)

    with open(public_key_path, 'r') as key_file:
        pub_key = key_file.read()

    logging.debug('Trying to import key')
    public_import_result = gpg.import_keys(pub_key)
    logging.debug(public_import_result)

    if public_import_result.count != 1:
        logging.error('Invalid public key provided, please provide 1 valid key')
        sys.exit(1)

    logging.info('Public key valid')


def importPrivateKey(gpg, sign_key):
    logging.info('Importing private key')

    private_import_result = gpg.import_keys(sign_key)

    if private_import_result.count != 1:
        logging.error('Invalid private key provided, please provide 1 valid key')
        sys.exit(1)

    logging.debug(private_import_result)

    if not any(data['ok'] >= '16' for data in private_import_result.results):
        logging.error('Key provided is not a secret key')
        sys.exit(1)

    private_key_id = private_import_result.results[0]['fingerprint']

    logging.info('Private key valid')

    logging.debug('Key id: {}'.format(private_key_id))

    logging.info('-- Done importing key --')

    return private_key_id
