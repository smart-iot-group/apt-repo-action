import os
import sys
import logging
import gnupg
import subprocess
from key import detectPublicKey, importPrivateKey

def transfer_file_over_scp(local_file_path, remote_file_path, hostname, port, private_key_str, scp_username=None):
    scp_dest = f'{hostname}:{remote_file_path}'
    if scp_username:
        scp_dest = f'{scp_username}@{scp_dest}'

    with tempfile.NamedTemporaryFile(prefix="scp_key_", delete=False) as tmp_key_file:
        tmp_key_file.write(private_key_str.encode())
        tmp_key_path = tmp_key_file.name

    scp_command = [
        'scp',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-P', str(port),
        '-i', tmp_key_path,
        local_file_path,
        scp_dest
    ]

    logging.info('Transferring file over SCP')
    try:
        subprocess.run(scp_command, check=True, universal_newlines=True)
        logging.info('File transferred successfully')
    except subprocess.CalledProcessError as e:
        logging.error(f'SCP transfer failed: {e}')
    finally:
        os.remove(tmp_key_path)
        logging.info('Temporary private key file removed')



debug = os.environ.get('INPUT_DEBUG', False)

if debug:
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
else:
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

if __name__ == '__main__':
    logging.info('-- Parsing input --')

    deb_file_path = os.environ.get('INPUT_FILE')
    key_public = os.environ.get('INPUT_PUBLIC_KEY')
    key_private = os.environ.get('INPUT_PRIVATE_KEY')
    key_passphrase = os.environ.get('INPUT_KEY_PASSPHRASE')

    if None in (deb_file_path, key_public, key_private):
        logging.error('Required key is missing')
        sys.exit(1)

    deb_file_path = deb_file_path.strip()

    logging.debug(deb_file_path)

    logging.info('-- Importing key --')
    
    repo_root = os.getcwd()
    gpg = gnupg.GPG()
    detectPublicKey(gpg, repo_root)
    
    private_key_id = importPrivateKey(gpg, key_private)

    logging.info('-- Done importing key --')

    # Sign the deb file
    logging.info('-- Signing .deb file --')
    gpg_command = [
        'gpg', '--batch', '--yes', '--pinentry-mode', 'loopback',
        '--passphrase-fd', '0', '--default-key', private_key_id,
        '--detach-sign', deb_file_path
    ]
    
    try:
        with subprocess.Popen(gpg_command, stdin=subprocess.PIPE, universal_newlines=True) as proc:
            proc.communicate(input=key_passphrase)
        logging.info('.deb file signed successfully')
    except subprocess.CalledProcessError as e:
        logging.error(f'Error signing .deb file: {e}')
        sys.exit(1)


    # SCP Transfer
    logging.info('-- Transferring files over SCP --')

    scp_hostname = os.environ.get('SCP_HOSTNAME')
    scp_port = int(os.environ.get('SCP_PORT', 22)) 
    scp_username = os.environ.get('SCP_USERNAME', None)
    apt_repo_private_key = os.environ.get('APT_REPO_PRIVATE')
    remote_file_path = os.environ.get('REMOTE_FILE_PATH')

    transfer_file_over_scp(deb_file_path, remote_file_path, scp_hostname, scp_port, apt_repo_private_key, scp_username)

    logging.info('-- Done transferring files --')
