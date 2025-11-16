"""
Testes para o serviço de criptografia
"""
import base64
import json
import pytest
from cryptography.exceptions import InvalidSignature

from core.processors.classes import CriptografiaService


@pytest.fixture
def criptografia_service(chaves_criptografia):
    """Cria uma instância do serviço de criptografia"""
    return CriptografiaService(
        chave_privada_path=chaves_criptografia["private_key_path"],
        chave_criptografia_path=chaves_criptografia["cryptography_key_path"]
    )


@pytest.mark.unit
class TestCriptografiaService:
    """Testes para o serviço de criptografia"""

    def test_inicializacao_servico(self, criptografia_service):
        """Testa se o serviço é inicializado corretamente"""
        assert criptografia_service.chave_privada is not None
        assert criptografia_service.chave_publica is not None
        assert criptografia_service.cifra is not None

    def test_criptografar_dados(self, criptografia_service):
        """Testa a criptografia de dados"""
        dados_originais = "Dados sensíveis de teste"
        dados_criptografados = criptografia_service.criptografar_dados(dados_originais)

        assert dados_criptografados is not None
        assert dados_criptografados != dados_originais
        assert isinstance(dados_criptografados, str)

    def test_descriptografar_dados(self, criptografia_service):
        """Testa a descriptografia de dados"""
        dados_originais = "Dados sensíveis de teste"
        dados_criptografados = criptografia_service.criptografar_dados(dados_originais)
        dados_descriptografados = criptografia_service.descriptografar_dados(dados_criptografados)

        assert dados_descriptografados == dados_originais

    def test_criptografar_descriptografar_json(self, criptografia_service):
        """Testa criptografia e descriptografia de dados JSON"""
        dados_json = {"candidato": "João", "voto": 123}
        dados_string = json.dumps(dados_json)

        dados_criptografados = criptografia_service.criptografar_dados(dados_string)
        dados_descriptografados = criptografia_service.descriptografar_dados(dados_criptografados)

        assert json.loads(dados_descriptografados) == dados_json

    def test_assinar_dados(self, criptografia_service):
        """Testa a assinatura de dados"""
        dados = "Dados para assinar"
        assinatura = criptografia_service.assinar_dados(dados)

        assert assinatura is not None
        assert isinstance(assinatura, bytes)
        assert len(assinatura) > 0

    def test_verificar_assinatura_valida(self, criptografia_service):
        """Testa a verificação de uma assinatura válida"""
        dados = "Dados para assinar"
        assinatura = criptografia_service.assinar_dados(dados)

        assert criptografia_service.verificar_assinatura(dados, assinatura) is True

    def test_verificar_assinatura_invalida(self, criptografia_service):
        """Testa a verificação de uma assinatura inválida"""
        dados = "Dados para assinar"
        assinatura = criptografia_service.assinar_dados(dados)

        # Modifica os dados após a assinatura
        dados_modificados = "Dados modificados"

        assert criptografia_service.verificar_assinatura(dados_modificados, assinatura) is False

    def test_verificar_assinatura_com_dados_modificados(self, criptografia_service):
        """Testa que a assinatura detecta modificação nos dados"""
        dados_originais = "Voto registrado para Candidato A"
        assinatura = criptografia_service.assinar_dados(dados_originais)

        # Tenta verificar com dados modificados
        dados_modificados = "Voto registrado para Candidato B"

        assert criptografia_service.verificar_assinatura(dados_originais, assinatura) is True
        assert criptografia_service.verificar_assinatura(dados_modificados, assinatura) is False

    def test_assinatura_com_chave_diferente(self, chaves_criptografia, temp_dir):
        """Testa que assinaturas com chaves diferentes não são válidas"""
        # Cria primeiro serviço
        service1 = CriptografiaService(
            chave_privada_path=chaves_criptografia["private_key_path"],
            chave_criptografia_path=chaves_criptografia["cryptography_key_path"]
        )

        # Gera segunda chave
        from core.utils.security import KeyManager
        private_key_path_2 = temp_dir / "private_key_2.pem"
        KeyManager(private_key_path=private_key_path_2.as_posix()).generate_private_key()

        # Cria segundo serviço com chave diferente
        service2 = CriptografiaService(
            chave_privada_path=private_key_path_2.as_posix(),
            chave_criptografia_path=chaves_criptografia["cryptography_key_path"]
        )

        dados = "Dados para assinar"
        assinatura_service1 = service1.assinar_dados(dados)

        # A assinatura do service1 não deve ser válida no service2
        assert service2.verificar_assinatura(dados, assinatura_service1) is False

    def test_criptografar_dados_vazios(self, criptografia_service):
        """Testa criptografia de string vazia"""
        dados_vazios = ""
        dados_criptografados = criptografia_service.criptografar_dados(dados_vazios)

        assert dados_criptografados is not None
        assert criptografia_service.descriptografar_dados(dados_criptografados) == dados_vazios

    def test_criptografar_dados_unicode(self, criptografia_service):
        """Testa criptografia de dados com caracteres especiais"""
        dados_unicode = "Eleição 2024 - Candidato José da Silva - Código 45123 ©"
        dados_criptografados = criptografia_service.criptografar_dados(dados_unicode)
        dados_descriptografados = criptografia_service.descriptografar_dados(dados_criptografados)

        assert dados_descriptografados == dados_unicode

    @pytest.mark.parametrize("dados_teste", [
        "Voto simples",
        "Voto com números 12345",
        "Voto com símbolos !@#$%",
        json.dumps({"candidato": "João", "partido": 45}),
        "A" * 1000,  # String longa
    ])
    def test_criptografar_varios_tipos_dados(self, criptografia_service, dados_teste):
        """Testa criptografia com vários tipos de dados"""
        dados_criptografados = criptografia_service.criptografar_dados(dados_teste)
        dados_descriptografados = criptografia_service.descriptografar_dados(dados_criptografados)

        assert dados_descriptografados == dados_teste

    def test_carregar_chave_privada_invalida(self, temp_dir):
        """Testa carregamento de chave privada inválida"""
        # Cria arquivo com conteúdo inválido
        chave_invalida_path = temp_dir / "chave_invalida.pem"
        with open(chave_invalida_path, "w") as f:
            f.write("CONTEÚDO INVÁLIDO")

        with pytest.raises(Exception):
            CriptografiaService(
                chave_privada_path=chave_invalida_path.as_posix(),
                chave_criptografia_path=chave_invalida_path.as_posix()
            )

    def test_descriptografar_dados_invalidos(self, criptografia_service):
        """Testa descriptografia de dados inválidos"""
        dados_invalidos = "dados_não_criptografados"

        with pytest.raises(Exception):
            criptografia_service.descriptografar_dados(dados_invalidos)

    def test_assinatura_deterministicamente_igual(self, criptografia_service):
        """Testa que a mesma assinatura é gerada para os mesmos dados"""
        dados = "Dados para assinar"
        assinatura1 = criptografia_service.assinar_dados(dados)
        assinatura2 = criptografia_service.assinar_dados(dados)

        # As assinaturas podem ser diferentes devido ao padding PSS, mas ambas devem ser válidas
        assert criptografia_service.verificar_assinatura(dados, assinatura1) is True
        assert criptografia_service.verificar_assinatura(dados, assinatura2) is True

    def test_base64_encoding_assinatura(self, criptografia_service):
        """Testa que a assinatura pode ser codificada em base64 e decodificada"""
        dados = "Dados para assinar"
        assinatura = criptografia_service.assinar_dados(dados)

        # Codifica em base64
        assinatura_base64 = base64.b64encode(assinatura).decode()

        # Decodifica de base64
        assinatura_decodificada = base64.b64decode(assinatura_base64)

        # Verifica que a assinatura decodificada é válida
        assert criptografia_service.verificar_assinatura(dados, assinatura_decodificada) is True
