import base64
import io
from typing import Dict, Any

import qrcode
from PIL import Image
from pyzbar.pyzbar import decode


class QrCode:
    """
    Classe para gerar e manipular códigos QR.

    Atributos:
        _qr_code (qrcode.QRCode): Instância do objeto QRCode da biblioteca qrcode.
        _image (PIL.Image.Image): Imagem do código QR gerado.
        _decode (None): Placeholder para futuras implementações de decodificação.

    Métodos:
        __init__(self, data='', version=1, box_size=20, border=1): Inicializa a classe QrCode.
        image(self): Retorna a imagem do código QR.
        as_base64(self): Retorna a imagem do código QR em formato base64.
        decode_from_file(file_name): Decodifica um código QR a partir de um arquivo de imagem.
        decode_from_image(blob_image): Decodifica um código QR a partir de uma imagem em memória.
    """

    def __init__(self, data: str = '', version: int = 1, box_size: int = 20, border: int = 1):
        """
        Inicializa a classe QrCode com os parâmetros fornecidos.

        Args:
            data (str): Dados a serem codificados no código QR.
            version (int): Versão do código QR (determina o tamanho).
            box_size (int): Tamanho de cada caixa do código QR.
            border (int): Tamanho da borda ao redor do código QR.

        Raises:
            ValueError: Se algum dos parâmetros fornecidos for inválido.
        """
        if not isinstance(data, str):
            raise ValueError("Data must be a string.")
        if not (1 <= version <= 40):
            raise ValueError("Version must be between 1 and 40.")
        if box_size <= 0:
            raise ValueError("Box size must be a positive integer.")
        if border < 0:
            raise ValueError("Border must be a non-negative integer.")

        self._qr_code = qrcode.QRCode(
            version=version,
            box_size=box_size,
            border=border
        )
        self._qr_code.add_data(data)
        self._qr_code.make()
        self._image = self._qr_code.make_image(fill='black', back_color='white')
        self._decode = None

    @property
    def image(self) -> Image.Image:
        """
        Retorna a imagem do código QR gerado.

        Returns:
            PIL.Image.Image: Imagem do código QR.
        """
        return self._image

    def as_base64(self) -> str:
        """
        Retorna a imagem do código QR em formato base64.

        Returns:
            str: String base64 representando a imagem do código QR.
        """
        buffer = io.BytesIO()
        self._image.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('ascii')

    @staticmethod
    def decode_from_file(file_name: str) -> Dict[str, Any]:
        """
        Decodifica um código QR a partir de um arquivo de imagem.

        Args:
            file_name (str): Caminho para o arquivo de imagem contendo o código QR.

        Returns:
            dict: Dicionário contendo os dados decodificados do código QR.

        Raises:
            FileNotFoundError: Se o arquivo não for encontrado.
            ValueError: Se a imagem não contiver um código QR válido.
        """
        try:
            image = Image.open(file_name)
        except FileNotFoundError:
            raise FileNotFoundError(f"File {file_name} not found.")

        decoded_data = decode(image)
        if not decoded_data:
            raise ValueError("No QR code found in the image.")

        return dict(decoded_data[0]._asdict())

    @staticmethod
    def decode_from_image(blob_image: Image.Image) -> Dict[str, Any]:
        """
        Decodifica um código QR a partir de uma imagem em memória.

        Args:
            blob_image (PIL.Image.Image): Imagem em memória contendo o código QR.

        Returns:
            dict: Dicionário contendo os dados decodificados do código QR.

        Raises:
            ValueError: Se a imagem não contiver um código QR válido.
        """
        decoded_data = decode(blob_image)
        if not decoded_data:
            raise ValueError("No QR code found in the image.")

        return dict(decoded_data[0]._asdict())


if __name__ == "__main__":
    import os

    # Dados a serem codificados no código QR
    data = "https://www.example.com"

    # Gerar o código QR
    qr = QrCode(data=data, version=1, box_size=10, border=4)

    # Salvar a imagem do código QR em um arquivo
    qr_image = qr.image
    qr_image_file = "qr_code.png"
    qr_image.save(qr_image_file)
    print(f"Código QR salvo em {qr_image_file}")
    try:
        # Exibir a imagem do código QR
        qr_image.show()

        # Decodificar o código QR a partir do arquivo
        decoded_data = QrCode.decode_from_file(qr_image_file)
        print("Dados decodificados do arquivo:", decoded_data)

        # Decodificar o código QR a partir da imagem em memória
        with Image.open(qr_image_file) as img:
            decoded_data_from_image = QrCode.decode_from_image(img)
            print("Dados decodificados da imagem:", decoded_data_from_image)
    finally:
        # Limpar o arquivo gerado
        os.remove(qr_image_file)
        print(f"Arquivo {qr_image_file} removido.")
