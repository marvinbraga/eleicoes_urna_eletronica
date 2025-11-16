"""
Testes para verificar se as fixtures estão funcionando corretamente
"""
import pytest
import os


def test_temp_dir_fixture(temp_dir):
    """Testa se o fixture temp_dir cria um diretório válido"""
    assert temp_dir.exists()
    assert temp_dir.is_dir()

    # Cria um arquivo de teste
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")
    assert test_file.exists()


def test_chaves_criptografia_fixture(chaves_criptografia):
    """Testa se o fixture chaves_criptografia gera chaves válidas"""
    assert "private_key_path" in chaves_criptografia
    assert "cryptography_key_path" in chaves_criptografia

    # Verifica se os arquivos existem
    assert os.path.exists(chaves_criptografia["private_key_path"])
    assert os.path.exists(chaves_criptografia["cryptography_key_path"])

    # Verifica se os arquivos não estão vazios
    assert os.path.getsize(chaves_criptografia["private_key_path"]) > 0
    assert os.path.getsize(chaves_criptografia["cryptography_key_path"]) > 0
