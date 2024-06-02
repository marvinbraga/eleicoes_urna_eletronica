from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


class KeyManager:
    def __init__(self, private_key_path: str):
        self.private_key_path = Path(private_key_path)
        self.private_key = None

    def generate_private_key(self):
        # Gera uma chave privada RSA de 2048 bits
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

    def save_private_key(self):
        if self.private_key is None:
            raise ValueError("A chave privada ainda não foi gerada.")

        # Serializa a chave privada em formato PEM
        pem_private_key = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Cria o diretório pai, se não existir
        self.private_key_path.parent.mkdir(parents=True, exist_ok=True)

        # Salva a chave privada em um arquivo
        with open(self.private_key_path, 'wb') as file:
            file.write(pem_private_key)

    def load_private_key(self):
        if not self.private_key_path.exists():
            raise FileNotFoundError(f"O arquivo da chave privada não existe: {self.private_key_path}")

        # Carrega a chave privada a partir do arquivo
        with open(self.private_key_path, 'rb') as file:
            pem_private_key = file.read()

        # Desserializa a chave privada
        self.private_key = serialization.load_pem_private_key(
            pem_private_key,
            password=None
        )

    def get_private_key(self):
        if self.private_key is None:
            raise ValueError("A chave privada ainda não foi gerada ou carregada.")

        return self.private_key


class CryptographyKeyManager:
    def __init__(self, key_path: str):
        self.key_path = Path(key_path)
        self.key = None

    def generate_key(self):
        # Gera uma nova chave de criptografia
        self.key = Fernet.generate_key()

    def save_key(self):
        if self.key is None:
            raise ValueError("A chave de criptografia ainda não foi gerada.")

        # Cria o diretório pai, se não existir
        self.key_path.parent.mkdir(parents=True, exist_ok=True)

        # Salva a chave de criptografia em um arquivo
        with open(self.key_path, 'wb') as file:
            file.write(self.key)

    def load_key(self):
        if not self.key_path.exists():
            raise FileNotFoundError(f"O arquivo da chave de criptografia não existe: {self.key_path}")

        # Carrega a chave de criptografia a partir do arquivo
        with open(self.key_path, 'rb') as file:
            self.key = file.read()

    def get_key(self):
        if self.key is None:
            raise ValueError("A chave de criptografia ainda não foi gerada ou carregada.")

        return self.key
