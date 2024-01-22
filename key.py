import logging
import os
import sys
import gnupg

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
    
    gpg = gnupg.GPG(use_agent=True, options=['--batch', '--pinentry-mode', 'loopback'])

    public_import_result = gpg.import_keys(pub_key)
    logging.debug(public_import_result)

    if len(public_import_result.fingerprints) != 1:
        logging.error('Invalid public key provided, please provide 1 valid key')
        sys.exit(1)


    logging.info('Public key valid')


def importPrivateKey(gpg, sign_key):
    logging.info('Importing private key')

    gpg = gnupg.GPG(use_agent=True, options=['--batch', '--pinentry-mode', 'loopback'])

    private_import_result = gpg.import_keys(sign_key)

    # Check if exactly one private key was imported
    if len(private_import_result.fingerprints) != 1:
        logging.error('Invalid private key provided, please provide 1 valid key')
        sys.exit(1)

    private_key_id = private_import_result.fingerprints[0]
    logging.info('Private key valid')
    logging.debug('Key id: {}'.format(private_key_id))

    logging.info('-- Done importing key --')

    return private_key_id
