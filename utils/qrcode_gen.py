# coding=utf-8
"""
QR Code Generator Module.
Marcus Vinicius Braga, 2021.
"""

import base64
import io

import qrcode
from PIL import Image
from pyzbar.pyzbar import decode


class QrCode(object):
    """
    Class to generate QRCode with versions 1 to 40.
    The "data" attribute must contain the information that will be encoded in the QRCode.
    """

    def __init__(self, data='', version=1, box_size=20, border=1):
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
    def image(self):
        """
        Retrieves the QRCode image.
        :return: Image.
        """
        return self._image

    def as_base64(self):
        """
        Returns the base64 code from the image field.
        :return: String base64.
        """
        buffer = io.BytesIO()
        self._image.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('ascii')

    # noinspection PyProtectedMember
    @staticmethod
    def decode_from_file(file_name):
        """
            Decodes QRCode image data.
            :param file_name: Physical path of the image.
            :return: Dictionary with information collected from QRCode.
        """
        return dict(decode(Image.open(file_name))[0]._asdict())

    # noinspection PyProtectedMember
    @staticmethod
    def decode_from_image(blob_image):
        """
            Decodes QRCode image data.
            :param blob_image: Image blob.
            :return: Dictionary with information collected from QRCode.
        """
        return dict(decode(blob_image)[0]._asdict())
