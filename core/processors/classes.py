# processors/classes.py
import base64
import hashlib
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List
from typing import Optional

from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from sklearn.ensemble import IsolationForest

from core.blockchain.classes import Blockchain
from core.models.classes import Voto, BoletimUrna, Candidato, RegistroImpresso, RegistroUrna, TotalizacaoVotos
from core.settings import ROOT_DIR
from core.utils.datetime import datetime_to_string


class IntegrityVerifier:
    """
    Classe responsável por verificar a integridade dos dados usando hash SHA-256.
    """

    def calculate_hash(self, data: str) -> str:
        """
        Calcula o hash SHA-256 dos dados fornecidos.

        :param data: Os dados para calcular o hash.
        :return: O hash SHA-256 dos dados.
        """
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_integrity(self, data: str, expected_hash: str) -> bool:
        """
        Verifica a integridade dos dados comparando o hash esperado com o hash calculado.

        :param data: Os dados para verificar a integridade.
        :param expected_hash: O hash esperado dos dados.
        :return: True se a integridade for verificada, False caso contrário.
        """
        actual_hash = self.calculate_hash(data)
        return actual_hash == expected_hash


class NonceGenerator:
    """
    Classe responsável por gerar um nonce (número único) usando UUID.
    """

    def generate_nonce(self) -> str:
        """
        Gera um nonce (número único) usando UUID.

        :return: O nonce gerado como uma string.
        """
        return str(uuid.uuid4())


class AuditLogger:
    """
    Classe responsável por registrar logs de auditoria em um arquivo.
    Implementa o padrão Singleton para garantir uma única instância da classe.
    """

    _instance: Optional['AuditLogger'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.logger = logging.getLogger('audit_logger')
            cls._instance.logger.setLevel(logging.INFO)
            # Obtém o timestamp atual com milissegundos
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            # Inclui o timestamp no nome do arquivo de log
            filename = ROOT_DIR / f'security/audit_{timestamp}.log'
            handler = logging.FileHandler(filename)
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            handler.setFormatter(formatter)
            cls._instance.logger.addHandler(handler)
        return cls._instance

    def log(self, message: str):
        """
        Registra uma mensagem de log de auditoria.

        :param message: A mensagem de log a ser registrada.
        """
        self.logger.info(message)


class CriptografiaService:
    """
    Classe responsável por fornecer serviços de criptografia e assinatura de dados.
    """

    def __init__(self, chave_privada_path: str, chave_criptografia_path: str):
        """
        Inicializa o serviço de criptografia com as chaves privada e de criptografia.

        :param chave_privada_path: O caminho para o arquivo da chave privada.
        :param chave_criptografia_path: O caminho para o arquivo da chave de criptografia.
        """
        self.chave_privada = self._carregar_chave_privada(chave_privada_path)
        self.chave_publica = self.chave_privada.public_key()
        self.cifra = self._carregar_cifra(chave_criptografia_path)

    def _carregar_chave_privada(self, chave_privada_path: str):
        """
        Carrega a chave privada a partir do arquivo.

        :param chave_privada_path: O caminho para o arquivo da chave privada.
        :return: A chave privada carregada.
        """
        with open(chave_privada_path, 'rb') as file:
            return serialization.load_pem_private_key(file.read(), password=None)

    def _carregar_cifra(self, chave_criptografia_path: str):
        """
        Carrega a cifra a partir do arquivo da chave de criptografia.

        :param chave_criptografia_path: O caminho para o arquivo da chave de criptografia.
        :return: A cifra carregada.
        """
        with open(chave_criptografia_path, 'rb') as file:
            chave_criptografia = file.read()
        return Fernet(chave_criptografia)

    def criptografar_dados(self, dados: str) -> str:
        """
        Criptografa os dados usando a cifra carregada.

        :param dados: Os dados a serem criptografados.
        :return: Os dados criptografados codificados em base64.
        """
        dados_criptografados = self.cifra.encrypt(dados.encode())
        return base64.b64encode(dados_criptografados).decode()

    def descriptografar_dados(self, dados_criptografados: str) -> str:
        """
        Descriptografa os dados criptografados usando a cifra carregada.

        :param dados_criptografados: Os dados criptografados codificados em base64.
        :return: Os dados descriptografados.
        """
        dados_criptografados_bytes = base64.b64decode(dados_criptografados)
        return self.cifra.decrypt(dados_criptografados_bytes).decode()

    def assinar_dados(self, dados: str) -> bytes:
        """
        Assina os dados usando a chave privada.

        :param dados: Os dados a serem assinados.
        :return: A assinatura dos dados.
        """
        return self.chave_privada.sign(
            dados.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )

    def verificar_assinatura(self, dados: str, assinatura: bytes) -> bool:
        """
        Verifica a assinatura dos dados usando a chave pública.

        :param dados: Os dados assinados.
        :param assinatura: A assinatura dos dados.
        :return: True se a assinatura for válida, False caso contrário.
        """
        try:
            self.chave_publica.verify(
                assinatura,
                dados.encode(),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            return False


class VotoService:
    """
    Serviço responsável por gerenciar o processo de votação.
    """

    def __init__(self, criptografia_service: CriptografiaService, blockchain: Blockchain,
                 integrity_verifier: IntegrityVerifier, nonce_generator: NonceGenerator,
                 audit_logger: AuditLogger):
        """
        Inicializa o serviço de votação com as dependências necessárias.

        :param criptografia_service: Serviço de criptografia.
        :param blockchain: Instância da blockchain.
        :param integrity_verifier: Verificador de integridade.
        :param nonce_generator: Gerador de nonce.
        :param audit_logger: Logger de auditoria.
        """
        self.criptografia_service = criptografia_service
        self.blockchain = blockchain
        self.integrity_verifier = integrity_verifier
        self.nonce_generator = nonce_generator
        self.audit_logger = audit_logger
        self.votos: List[Voto] = []

    def votar(self, candidato: Candidato) -> Voto:
        """
        Realiza um voto para um candidato.

        :param candidato: O candidato a ser votado.
        :return: O voto registrado.
        """
        # Cria um novo voto com os dados do candidato e informações adicionais
        voto = Voto(
            id=len(self.votos) + 1,
            candidato=candidato,
            hash_localizacao=self.blockchain.chain[-1].hash,
            hash_blockchain=self.blockchain.chain[-1].hash,
            qr_code=f"qrcode_{len(self.votos) + 1}",
            nonce=self.nonce_generator.generate_nonce()
        )

        # Converte o voto para JSON
        voto_json = voto.json()

        # Assina o voto usando o serviço de criptografia
        assinatura = self.criptografia_service.assinar_dados(voto_json)

        # Cria um objeto contendo o voto e a assinatura
        voto_assinado = {
            "voto": voto_json,
            "assinatura": base64.b64encode(assinatura).decode()
        }

        # Criptografa o voto assinado usando o serviço de criptografia
        voto_criptografado = self.criptografia_service.criptografar_dados(json.dumps(voto_assinado))

        # Adiciona o voto à lista de votos
        self.votos.append(voto)

        # Adiciona o voto criptografado como uma transação na blockchain
        self.blockchain.add_transaction(voto_criptografado)

        # Minera as transações pendentes na blockchain
        self.blockchain.mine_pending_transactions()

        # Registra o voto no logger de auditoria
        self.audit_logger.log(f"Voto registrado: {voto}")

        return voto

    def validar_votos(self, registros_impressos: List[RegistroImpresso]) -> bool:
        """
        Valida os votos comparando-os com os registros impressos.

        :param registros_impressos: Lista de registros impressos.
        :return: True se todos os votos forem válidos, False caso contrário.
        """
        for registro in registros_impressos:
            # Procura o voto correspondente ao registro impresso
            voto = next((v for v in self.votos if v.id == registro.voto.id), None)

            # Verifica se o voto existe e se os atributos relevantes correspondem ao registro impresso
            if voto is None or voto.id != registro.voto.id or voto.candidato != registro.voto.candidato:
                return False

            # Verifica a integridade do voto comparando o hash do registro impresso com o hash calculado
            # a partir dos dados do voto eletrônico
            voto_json = voto.json()
            expected_hash = self.integrity_verifier.calculate_hash(voto_json)
            if not self.integrity_verifier.verify_integrity(registro.voto.json(), expected_hash):
                return False

        return True

    def processar_votos(self, votos: List[Voto]):
        """
        Processa os votos recebidos.

        :param votos: Lista de votos a serem processados.
        """
        for voto_criptografado in votos:
            # Descriptografa o voto usando o serviço de criptografia
            voto_descriptografado = self.criptografia_service.descriptografar_dados(voto_criptografado)

            # Converte o voto descriptografado de JSON para um objeto Python
            voto_assinado = json.loads(voto_descriptografado)

            # Extrai o JSON do voto e a assinatura do objeto voto_assinado
            voto_json = voto_assinado["voto"]
            assinatura = base64.b64decode(voto_assinado["assinatura"])

            # Verifica a assinatura do voto usando o serviço de criptografia
            if self.criptografia_service.verificar_assinatura(voto_json, assinatura):
                # Converte o JSON do voto para um objeto Voto
                voto = Voto.parse_raw(voto_json)

                # Verifica se o nonce do voto já existe na lista de votos
                if voto.nonce not in [v.nonce for v in self.votos]:
                    # Adiciona o voto à lista de votos
                    self.votos.append(voto)

                    # Adiciona o voto criptografado como uma transação na blockchain
                    self.blockchain.add_transaction(voto_criptografado)
                else:
                    # Registra uma tentativa de voto duplicado no logger de auditoria
                    self.audit_logger.log(f"Tentativa de voto duplicado: {voto}")
            else:
                # Registra um voto inválido no logger de auditoria
                self.audit_logger.log(f"Voto inválido: assinatura não confere - {voto_json}")

        # Minera as transações pendentes na blockchain
        self.blockchain.mine_pending_transactions()


class BoletimUrnaService:
    """
    Serviço responsável por gerenciar os boletins de urna.
    """

    def __init__(self, criptografia_service: CriptografiaService, voto_service: VotoService):
        """
        Inicializa o serviço de boletim de urna com as dependências necessárias.

        :param criptografia_service: Serviço de criptografia.
        :param voto_service: Serviço de votação.
        """
        self.criptografia_service = criptografia_service
        self.voto_service = voto_service
        self.boletins_urna: List[BoletimUrna] = []

    def gerar_boletim_urna(self) -> BoletimUrna:
        """
        Gera um novo boletim de urna com base nos votos registrados.

        :return: O boletim de urna gerado.
        """
        # Cria um novo boletim de urna com os dados relevantes
        boletim = BoletimUrna(
            id=len(self.boletins_urna) + 1,
            secao="Seção XYZ",
            zona="Zona 123",
            municipio="Município ABC",
            estado="Estado MN",
            data_hora=datetime.now(),
            hash_final_blockchain=self.voto_service.blockchain.chain[-1].hash,
            hash_bu=self.voto_service.blockchain.chain[-1].hash,
            qr_code=f"qrcode_bu_{len(self.boletins_urna) + 1}",
            votos=self.voto_service.votos
        )

        # Converte o boletim para um dicionário, excluindo os campos None
        boletim_dict = boletim.dict(exclude_none=True)

        # Assina o boletim usando o serviço de criptografia
        assinatura_boletim = self.criptografia_service.assinar_dados(
            json.dumps(boletim_dict, default=datetime_to_string, sort_keys=True))

        # Adiciona a assinatura codificada em base64 ao boletim
        boletim.assinatura = base64.b64encode(assinatura_boletim).decode()

        # Criptografa o boletim usando o serviço de criptografia
        boletim_criptografado = self.criptografia_service.criptografar_dados(boletim.json())

        # Adiciona o boletim à lista de boletins de urna
        self.boletins_urna.append(boletim)

        return boletim

    def validar_boletim_urna(self, boletim_impresso: BoletimUrna) -> bool:
        """
        Valida um boletim de urna impresso comparando-o com o boletim de urna eletrônico correspondente.

        :param boletim_impresso: O boletim de urna impresso a ser validado.
        :return: True se o boletim de urna for válido, False caso contrário.
        """
        # Procura o boletim de urna eletrônico correspondente ao boletim impresso
        boletim_eletronico = next((b for b in self.boletins_urna if b.id == boletim_impresso.id), None)

        # Se o boletim eletrônico não for encontrado, retorna False
        if boletim_eletronico is None:
            return False

        # Converte o boletim eletrônico para um dicionário, excluindo o campo 'assinatura'
        boletim_dict = boletim_eletronico.dict(exclude_none=True, exclude={'assinatura'})

        # Decodifica a assinatura do boletim eletrônico a partir da base64
        assinatura_boletim = base64.b64decode(boletim_eletronico.assinatura)

        # Verifica a assinatura do boletim usando o serviço de criptografia
        return self.criptografia_service.verificar_assinatura(
            json.dumps(boletim_dict, default=datetime_to_string, sort_keys=True),
            assinatura_boletim
        )


class TotalizacaoVotosService:
    """
    Serviço responsável por totalizar os votos e verificar a integridade da totalização.
    """

    def __init__(self, criptografia_service: CriptografiaService, voto_service: VotoService,
                 audit_logger: AuditLogger):
        """
        Inicializa o serviço de totalização de votos com as dependências necessárias.

        :param criptografia_service: Serviço de criptografia.
        :param voto_service: Serviço de votação.
        :param audit_logger: Logger de auditoria.
        """
        self.criptografia_service = criptografia_service
        self.voto_service = voto_service
        self.audit_logger = audit_logger

    def totalizar_votos(self) -> TotalizacaoVotos:
        """
        Totaliza os votos e retorna o resultado da totalização.

        :return: O resultado da totalização dos votos.
        """
        tally = self._contabilizar_votos()
        votos_totalizados = self._gerar_votos_totalizados(tally)
        totalizacao = self._criar_totalizacao_votos(votos_totalizados)
        self._assinar_totalizacao(totalizacao)
        return totalizacao

    def _contabilizar_votos(self) -> dict:
        """
        Contabiliza os votos válidos a partir da blockchain.

        :return: Um dicionário com a contagem de votos por candidato.
        """
        tally = {}
        for block in self.voto_service.blockchain.chain:
            for transaction in block.transactions:
                voto = self._obter_voto_valido(transaction)
                if voto:
                    self._atualizar_contagem_votos(tally, voto)
        return tally

    def _obter_voto_valido(self, transaction: str) -> Voto:
        """
        Obtém um voto válido a partir de uma transação na blockchain.

        :param transaction: A transação contendo o voto criptografado.
        :return: O voto válido, se a assinatura for válida, ou None caso contrário.
        """
        voto_descriptografado = self.criptografia_service.descriptografar_dados(transaction)
        voto_assinado = json.loads(voto_descriptografado)
        voto_json = voto_assinado["voto"]
        assinatura = base64.b64decode(voto_assinado["assinatura"])

        if self.criptografia_service.verificar_assinatura(voto_json, assinatura):
            return Voto.parse_raw(voto_json)
        else:
            print("Voto inválido: assinatura não confere")
            return None

    def _atualizar_contagem_votos(self, tally: dict, voto: Voto):
        """
        Atualiza a contagem de votos para um candidato específico.

        :param tally: O dicionário de contagem de votos.
        :param voto: O voto a ser contabilizado.
        """
        candidato_id = voto.candidato.id
        if candidato_id in tally:
            tally[candidato_id]["votos"] += 1
        else:
            tally[candidato_id] = {
                "candidato": voto.candidato,
                "votos": 1,
                "hash_localizacao": voto.hash_localizacao,
                "hash_blockchain": voto.hash_blockchain,
                "qr_code": voto.qr_code
            }

    def _gerar_votos_totalizados(self, tally: dict) -> List[Voto]:
        """
        Gera a lista de votos totalizados a partir da contagem de votos.

        :param tally: O dicionário de contagem de votos.
        :return: A lista de votos totalizados.
        """
        votos_totalizados = []
        for candidato_id, dados_voto in tally.items():
            voto_totalizado = Voto(
                id=candidato_id,
                candidato=dados_voto["candidato"],
                hash_localizacao=dados_voto["hash_localizacao"],
                hash_blockchain=dados_voto["hash_blockchain"],
                qr_code=dados_voto["qr_code"]
            )
            votos_totalizados.append(voto_totalizado)
        return votos_totalizados

    def _criar_totalizacao_votos(self, votos_totalizados: List[Voto]) -> TotalizacaoVotos:
        """
        Cria um objeto de totalização de votos com base nos votos totalizados.

        :param votos_totalizados: A lista de votos totalizados.
        :return: O objeto de totalização de votos.
        """
        return TotalizacaoVotos(
            id=1,
            data_hora=datetime.now(),
            votos_totalizados=votos_totalizados,
            hash_blockchain=self.voto_service.blockchain.chain[-1].hash
        )

    def _assinar_totalizacao(self, totalizacao: TotalizacaoVotos):
        """
        Assina a totalização de votos e registra a assinatura no logger de auditoria.

        :param totalizacao: O objeto de totalização de votos a ser assinado.
        """
        totalizacao_dict = totalizacao.dict(exclude_none=True)
        assinatura_totalizacao = self.criptografia_service.assinar_dados(
            json.dumps(totalizacao_dict, default=datetime_to_string, sort_keys=True))
        totalizacao.assinatura = base64.b64encode(assinatura_totalizacao).decode()
        self.audit_logger.log(f"Totalização de votos assinada: {totalizacao}")

    def verificar_integridade_totalizacao(self, totalizacao: TotalizacaoVotos) -> bool:
        """
        Verifica a integridade da totalização de votos comparando a assinatura.

        :param totalizacao: O objeto de totalização de votos a ser verificado.
        :return: True se a assinatura for válida, False caso contrário.
        """
        totalizacao_dict = totalizacao.dict(exclude_none=True, exclude={'assinatura'})
        assinatura_totalizacao = base64.b64decode(totalizacao.assinatura)
        return self.criptografia_service.verificar_assinatura(
            json.dumps(totalizacao_dict, default=datetime_to_string, sort_keys=True),
            assinatura_totalizacao,
        )


class AnomaliaService:
    """
    Serviço responsável por detectar anomalias e conluio nos votos usando o algoritmo Isolation Forest.
    """

    def __init__(self):
        """
        Inicializa o serviço de detecção de anomalias com os parâmetros do Isolation Forest.
        """
        self.isolation_forest = IsolationForest(n_estimators=100, contamination=0.1)

    def _extrair_caracteristicas(self, voto):
        """
        Extrai as características relevantes de um voto para detecção de anomalias.

        :param voto: O voto a ser analisado.
        :return: Uma lista contendo as características extraídas do voto.
        """
        candidato_id = voto.candidato.id
        hash_localizacao = hash(voto.hash_localizacao) % 1000000
        hash_blockchain = hash(voto.hash_blockchain) % 1000000
        return [candidato_id, hash_localizacao, hash_blockchain]

    def detectar_anomalias(self, votos):
        """
        Detecta anomalias nos votos usando o algoritmo Isolation Forest.

        :param votos: A lista de votos a serem analisados.
        :return: Uma lista contendo os votos considerados anômalos.
        """
        # Extrai as características dos votos
        caracteristicas = [self._extrair_caracteristicas(voto) for voto in votos]

        # Treina o modelo Isolation Forest com as características dos votos
        self.isolation_forest.fit(caracteristicas)

        # Calcula os scores de anomalia para cada voto
        anomaly_scores = self.isolation_forest.decision_function(caracteristicas)

        # Identifica os votos anômalos com base nos scores de anomalia
        anomalias = [voto for voto, score in zip(votos, anomaly_scores) if score < 0]

        return anomalias

    def detectar_conluio(self, votos):
        """
        Detecta possíveis casos de conluio nos votos usando o algoritmo Isolation Forest.

        :param votos: A lista de votos a serem analisados.
        :return: Uma lista contendo os votos suspeitos de conluio.
        """
        # Extrai as características dos votos
        caracteristicas = [self._extrair_caracteristicas(voto) for voto in votos]

        # Treina o modelo Isolation Forest com as características dos votos
        self.isolation_forest.fit(caracteristicas)

        # Calcula os scores de anomalia para cada voto
        anomaly_scores = self.isolation_forest.decision_function(caracteristicas)

        # Identifica os votos suspeitos de conluio com base em um threshold mais restritivo
        conluio_suspeito = [voto for voto, score in zip(votos, anomaly_scores) if score < -0.5]

        return conluio_suspeito


class SistemaVotacao:
    """
    Classe principal do sistema de votação, responsável por coordenar os serviços e funcionalidades.
    """

    def __init__(self, chave_privada_path: str, chave_criptografia_path: str):
        """
        Inicializa o sistema de votação com os serviços necessários.

        :param chave_privada_path: Caminho para a chave privada.
        :param chave_criptografia_path: Caminho para a chave de criptografia.
        """
        self.criptografia_service = CriptografiaService(chave_privada_path, chave_criptografia_path)
        self.blockchain = Blockchain()
        self.integrity_verifier = IntegrityVerifier()
        self.nonce_generator = NonceGenerator()
        self.audit_logger = AuditLogger()
        self.voto_service = VotoService(self.criptografia_service, self.blockchain,
                                        self.integrity_verifier, self.nonce_generator,
                                        self.audit_logger)
        self.boletim_urna_service = BoletimUrnaService(self.criptografia_service, self.voto_service)
        self.totalizacao_votos_service = TotalizacaoVotosService(
            self.criptografia_service, self.voto_service,
            self.audit_logger
        )
        self.anomalia_service = AnomaliaService()

    def votar(self, candidato: Candidato) -> Voto:
        """
        Realiza a votação para um candidato.

        :param candidato: O candidato escolhido pelo eleitor.
        :return: O voto registrado.
        """
        return self.voto_service.votar(candidato)

    def gerar_registro_impresso(self, voto: Voto) -> RegistroImpresso:
        """
        Gera um registro impresso do voto.

        :param voto: O voto a ser impresso.
        :return: O registro impresso do voto.
        """
        return RegistroImpresso(voto=voto, data_hora=datetime.now())

    def validar_votos(self, registros_impressos: List[RegistroImpresso]) -> bool:
        """
        Valida os votos a partir dos registros impressos.

        :param registros_impressos: Lista de registros impressos dos votos.
        :return: True se todos os votos forem válidos, False caso contrário.
        """
        return self.voto_service.validar_votos(registros_impressos)

    def gerar_boletim_urna(self) -> BoletimUrna:
        """
        Gera o boletim de urna.

        :return: O boletim de urna gerado.
        """
        return self.boletim_urna_service.gerar_boletim_urna()

    def validar_boletim_urna(self, boletim_impresso: BoletimUrna) -> bool:
        """
        Valida o boletim de urna impresso.

        :param boletim_impresso: O boletim de urna impresso a ser validado.
        :return: True se o boletim de urna for válido, False caso contrário.
        """
        return self.boletim_urna_service.validar_boletim_urna(boletim_impresso)

    def gerar_registro_urna(self, boletim_urna: BoletimUrna) -> RegistroUrna:
        """
        Gera um registro de urna a partir do boletim de urna.

        :param boletim_urna: O boletim de urna a ser registrado.
        :return: O registro de urna gerado.
        """
        return RegistroUrna(
            id=len(self.boletim_urna_service.boletins_urna),
            data_hora=datetime.now(),
            boletim_urna_escaneado=b"dados_escaneados",
            boletim_urna_eletronico=boletim_urna
        )

    def totalizar_votos(self) -> TotalizacaoVotos:
        """
        Realiza a totalização dos votos.

        :return: O resultado da totalização dos votos.
        """
        return self.totalizacao_votos_service.totalizar_votos()

    def verificar_integridade_totalizacao(self, totalizacao: TotalizacaoVotos) -> bool:
        """
        Verifica a integridade da totalização dos votos.

        :param totalizacao: A totalização dos votos a ser verificada.
        :return: True se a totalização for íntegra, False caso contrário.
        """
        return self.totalizacao_votos_service.verificar_integridade_totalizacao(totalizacao)

    def detectar_anomalias(self, votos):
        """
        Detecta anomalias nos votos.

        :param votos: Lista de votos a serem analisados.
        :return: Lista de votos considerados anômalos.
        """
        return self.anomalia_service.detectar_anomalias(votos)

    def detectar_conluio(self, votos):
        """
        Detecta possíveis casos de conluio nos votos.

        :param votos: Lista de votos a serem analisados.
        :return: Lista de votos suspeitos de conluio.
        """
        return self.anomalia_service.detectar_conluio(votos)
