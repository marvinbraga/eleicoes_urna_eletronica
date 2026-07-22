#!/usr/bin/env python3
"""Generate local election crypto keys. Writes gitignored PEM files under resources/."""
from __future__ import annotations

from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    resources = root / "resources"
    resources.mkdir(exist_ok=True)

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    (resources / "private_key.pem").write_bytes(pem)
    (resources / "cryptography_key.pem").write_text(
        Fernet.generate_key().decode() + "\n", encoding="utf-8"
    )
    print("Wrote resources/private_key.pem and resources/cryptography_key.pem (gitignored).")


if __name__ == "__main__":
    main()
