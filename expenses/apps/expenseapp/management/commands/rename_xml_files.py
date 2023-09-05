from django.core.management.base import BaseCommand
import os
import paramiko

class Command (BaseCommand):
    help = 'Rename wrongly named XML on vero SFTP server'

    def handle(self, *args, **options):
        IR_USER = os.getenv('IR_USER')
        IR_SERVER = os.getenv('IR_SERVER')
        IR_PORT = 22
        key = paramiko.RSAKey.from_private_key_file(
            'vero-key-test.pem', password=os.getenv('VERO_PRIVATE_KEY_PASSPHRASE'))

        transport = paramiko.Transport((
            IR_SERVER,
            IR_PORT
        ))
        transport.connect(
            username=IR_USER,
            pkey=key
        )
        sftp = paramiko.SFTPClient.from_transport(transport)

        filenames = sftp.listdir(f'IN')
        for filename in filenames:
            if 'tmp' in filename:
                sftp.rename(filename, filename.replaec('tmp', 'xml'))
