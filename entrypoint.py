import os
import sys
import logging
import subprocess
from key import detectPublicKey, importPrivateKey
import tempfile
import paramiko
from paramiko import SSHClient
from paramiko import Agent
from scp import SCPClient
import io


def scp_transfer(hostname, port, local_file_path, remote_file_path):
    ssh_auth_sock = os.getenv('SSH_AUTH_SOCK', None)
    if ssh_auth_sock is None:
        raise ValueError("SSH_AUTH_SOCK environment variable is not set")

    logging.info(f"SSH_AUTH_SOCK: {ssh_auth_sock}")

    if not os.path.exists(ssh_auth_sock):
        raise ValueError(f"SSH agent socket {ssh_auth_sock} does not exist")
    else:
        logging.info("SSH agent socket exists")

    agent = paramiko.Agent()
    agent_keys = agent.get_keys()
    logging.info(f"Agent keys: {agent_keys}")

    if not agent_keys:
        raise ValueError("No keys available in SSH agent")

    for key in agent_keys:
        logging.info(f"Key type: {key.get_name()}, Key blob: {key.get_fingerprint()}")


    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname, port=int(port), pkey=agent_keys[0])
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
    detectPublicKey(repo_root)
    
    private_key_id = importPrivateKey(key_private)

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

    scp_transfer(scp_hostname, scp_port, scp_username, deb_file_path, remote_file_path, )

    logging.info('-- Done transferring files --')
