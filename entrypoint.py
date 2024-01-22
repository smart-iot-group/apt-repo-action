import os
import sys
import logging
import gnupg
import subprocess
from key import detectPublicKey, importPrivateKey
import tempfile
import paramiko
from paramiko import SSHClient
from paramiko import Agent
from scp import SCPClient
import io

def scp_transfer(hostname, port, username, local_file_path, remote_file_path):
    ssh_auth_sock = os.getenv('SSH_AUTH_SOCK', None)
    if ssh_auth_sock is None:
        raise ValueError("SSH_AUTH_SOCK environment variable is not set")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect using the SSH agent
        client.connect(hostname, port=int(port), username=username, sock=paramiko.AgentRequestHandler(ssh_auth_sock))

        # SCP transfer
        with SCPClient(client.get_transport()) as scp:
            scp.put(local_file_path, remote_file_path)

    finally:
        client.close()

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

    scp_hostname = os.environ.get('INPUT_SCP_HOSTNAME')
    scp_port = int(os.environ.get('INPUT_SCP_PORT', 22))
    scp_username = os.environ.get('INPUT_SCP_USERNAME', None)
    remote_file_path = os.environ.get('INPUT_REMOTE_FILE_PATH')

    transfer_file_over_scp(deb_file_path, remote_file_path, scp_hostname, scp_port, scp_username)

    logging.info('-- Done transferring files --')
