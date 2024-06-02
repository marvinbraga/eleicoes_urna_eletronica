# processors/classes.py
import base64
import json
from datetime import datetime
from typing import List

from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from sklearn.ensemble import IsolationForest

from blockchain.classes import Blockchain
from models.classes import Voto, BoletimUrna, Candidato, RegistroImpresso, RegistroUrna, TotalizacaoVotos
from utils.datetime import datetime_to_string


class CriptografiaService:
    def __init__(self, chave_privada_path: str, chave_criptografia_path: str):
        self.chave_privada = self._carregar_chave_privada(chave_privada_path)
        self.chave_publica = self.chave_privada.public_key()
        self.cifra = self._carregar_cifra(chave_criptografia_path)

    def _carregar_chave_privada(self, chave_privada_path: str):
        with open(chave_privada_path, 'rb') as file:
            return serialization.load_pem_private_key(file.read(), password=None)

    def _carregar_cifra(self, chave_criptografia_path: str):
        with open(chave_criptografia_path, 'rb') as file:
            chave_criptografia = file.read()
        return Fernet(chave_criptografia)

    def criptografar_dados(self, dados: str) -> str:
        dados_criptografados = self.cifra.encrypt(dados.encode())
        return base64.b64encode(dados_criptografados).decode()

    def descriptografar_dados(self, dados_criptografados: str) -> str:
        dados_criptografados_bytes = base64.b64decode(dados_criptografados)
        return self.cifra.decrypt(dados_criptografados_bytes).decode()

    def assinar_dados(self, dados: str) -> bytes:
        return self.chave_privada.sign(
            dados.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )

    def verificar_assinatura(self, dados: str, assinatura: bytes) -> bool:
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
    def __init__(self, criptografia_service: CriptografiaService, blockchain: Blockchain):
        self.criptografia_service = criptografia_service
        self.blockchain = blockchain
        self.votos: List[Voto] = []

    def votar(self, candidato: Candidato) -> Voto:
        voto = Voto(
            id=len(self.votos) + 1,
            candidato=candidato,
            hash_localizacao=self.blockchain.chain[-1].hash,
            hash_blockchain=self.blockchain.chain[-1].hash,
            qr_code=f"qrcode_{len(self.votos) + 1}"
        )
        voto_json = voto.json()
        assinatura = self.criptografia_service.assinar_dados(voto_json)
        voto_assinado = {
            "voto": voto_json,
            "assinatura": base64.b64encode(assinatura).decode()
        }
        voto_criptografado = self.criptografia_service.criptografar_dados(json.dumps(voto_assinado))
        self.votos.append(voto)
        self.blockchain.add_transaction(voto_criptografado)
        self.blockchain.mine_pending_transactions()
        return voto

    def validar_votos(self, registros_impressos: List[RegistroImpresso]) -> bool:
        for registro in registros_impressos:
            voto = next((v for v in self.votos if v.id == registro.voto.id), None)
            if voto is None or voto.dict() != registro.voto.dict():
                return False
        return True

    def processar_votos(self, votos: List[Voto]):
        for voto_criptografado in votos:
            voto_descriptografado = self.criptografia_service.descriptografar_dados(voto_criptografado)
            voto_assinado = json.loads(voto_descriptografado)
            voto_json = voto_assinado["voto"]
            assinatura = base64.b64decode(voto_assinado["assinatura"])

            if self.criptografia_service.verificar_assinatura(voto_json, assinatura):
                voto = Voto.parse_raw(voto_json)
                self.votos.append(voto)
                self.blockchain.add_transaction(voto_criptografado)
            else:
                print("Voto inválido: assinatura não confere")

        self.blockchain.mine_pending_transactions()


class BoletimUrnaService:
    def __init__(self, criptografia_service: CriptografiaService, voto_service: VotoService):
        self.criptografia_service = criptografia_service
        self.voto_service = voto_service
        self.boletins_urna: List[BoletimUrna] = []

    def gerar_boletim_urna(self) -> BoletimUrna:
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

        boletim_dict = boletim.dict(exclude_none=True)
        assinatura_boletim = self.criptografia_service.assinar_dados(
            json.dumps(boletim_dict, default=datetime_to_string, sort_keys=True))
        boletim.assinatura = base64.b64encode(assinatura_boletim).decode()

        boletim_criptografado = self.criptografia_service.criptografar_dados(boletim.json())
        self.boletins_urna.append(boletim)
        return boletim

    def validar_boletim_urna(self, boletim_impresso: BoletimUrna) -> bool:
        boletim_eletronico = next((b for b in self.boletins_urna if b.id == boletim_impresso.id), None)

        if boletim_eletronico is None:
            return False

        boletim_dict = boletim_eletronico.dict(exclude_none=True, exclude={'assinatura'})
        assinatura_boletim = base64.b64decode(boletim_eletronico.assinatura)
        return self.criptografia_service.verificar_assinatura(
            json.dumps(boletim_dict, default=datetime_to_string, sort_keys=True),
            assinatura_boletim
        )


class TotalizacaoVotosService:
    def __init__(self, criptografia_service: CriptografiaService, voto_service: VotoService):
        self.criptografia_service = criptografia_service
        self.voto_service = voto_service

    def totalizar_votos(self) -> TotalizacaoVotos:
        tally = self._contabilizar_votos()
        votos_totalizados = self._gerar_votos_totalizados(tally)
        totalizacao = self._criar_totalizacao_votos(votos_totalizados)
        self._assinar_totalizacao(totalizacao)
        return totalizacao

    def _contabilizar_votos(self) -> dict:
        tally = {}
        for block in self.voto_service.blockchain.chain:
            for transaction in block.transactions:
                voto = self._obter_voto_valido(transaction)
                if voto:
                    self._atualizar_contagem_votos(tally, voto)
        return tally

    def _obter_voto_valido(self, transaction: str) -> Voto:
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
        return TotalizacaoVotos(
            id=1,
            data_hora=datetime.now(),
            votos_totalizados=votos_totalizados,
            hash_blockchain=self.voto_service.blockchain.chain[-1].hash
        )

    def _assinar_totalizacao(self, totalizacao: TotalizacaoVotos):
        totalizacao_dict = totalizacao.dict(exclude_none=True)
        assinatura_totalizacao = self.criptografia_service.assinar_dados(
            json.dumps(totalizacao_dict, default=datetime_to_string, sort_keys=True))
        totalizacao.assinatura = base64.b64encode(assinatura_totalizacao).decode()

    def verificar_integridade_totalizacao(self, totalizacao: TotalizacaoVotos) -> bool:
        totalizacao_dict = totalizacao.dict(exclude_none=True, exclude={'assinatura'})
        assinatura_totalizacao = base64.b64decode(totalizacao.assinatura)
        return self.criptografia_service.verificar_assinatura(
            json.dumps(totalizacao_dict, default=datetime_to_string, sort_keys=True),
            assinatura_totalizacao,
        )


class AnomaliaService:
    def __init__(self):
        self.isolation_forest = IsolationForest(n_estimators=100, contamination=0.1)

    def _extrair_caracteristicas(self, voto):
        candidato_id = voto.candidato.id
        hash_localizacao = hash(voto.hash_localizacao) % 1000000
        hash_blockchain = hash(voto.hash_blockchain) % 1000000
        return [candidato_id, hash_localizacao, hash_blockchain]

    def detectar_anomalias(self, votos):
        caracteristicas = [self._extrair_caracteristicas(voto) for voto in votos]
        self.isolation_forest.fit(caracteristicas)
        anomaly_scores = self.isolation_forest.decision_function(caracteristicas)
        anomalias = [voto for voto, score in zip(votos, anomaly_scores) if score < 0]
        return anomalias

    def detectar_conluio(self, votos):
        caracteristicas = [self._extrair_caracteristicas(voto) for voto in votos]
        self.isolation_forest.fit(caracteristicas)
        anomaly_scores = self.isolation_forest.decision_function(caracteristicas)
        conluio_suspeito = [voto for voto, score in zip(votos, anomaly_scores) if score < -0.5]
        return conluio_suspeito


class SistemaVotacao:
    def __init__(self, chave_privada_path: str, chave_criptografia_path: str):
        self.criptografia_service = CriptografiaService(chave_privada_path, chave_criptografia_path)
        self.blockchain = Blockchain()
        self.voto_service = VotoService(self.criptografia_service, self.blockchain)
        self.boletim_urna_service = BoletimUrnaService(self.criptografia_service, self.voto_service)
        self.totalizacao_votos_service = TotalizacaoVotosService(self.criptografia_service, self.voto_service)
        self.anomalia_service = AnomaliaService()

    def votar(self, candidato: Candidato) -> Voto:
        return self.voto_service.votar(candidato)

    def gerar_registro_impresso(self, voto: Voto) -> RegistroImpresso:
        return RegistroImpresso(voto=voto, data_hora=datetime.now())

    def validar_votos(self, registros_impressos: List[RegistroImpresso]) -> bool:
        return self.voto_service.validar_votos(registros_impressos)

    def gerar_boletim_urna(self) -> BoletimUrna:
        return self.boletim_urna_service.gerar_boletim_urna()

    def validar_boletim_urna(self, boletim_impresso: BoletimUrna) -> bool:
        return self.boletim_urna_service.validar_boletim_urna(boletim_impresso)

    def gerar_registro_urna(self, boletim_urna: BoletimUrna) -> RegistroUrna:
        return RegistroUrna(
            id=len(self.boletim_urna_service.boletins_urna),
            data_hora=datetime.now(),
            boletim_urna_escaneado=b"dados_escaneados",
            boletim_urna_eletronico=boletim_urna
        )

    def totalizar_votos(self) -> TotalizacaoVotos:
        return self.totalizacao_votos_service.totalizar_votos()

    def verificar_integridade_totalizacao(self, totalizacao: TotalizacaoVotos) -> bool:
        return self.totalizacao_votos_service.verificar_integridade_totalizacao(totalizacao)

    def detectar_anomalias(self, votos):
        return self.anomalia_service.detectar_anomalias(votos)

    def detectar_conluio(self, votos):
        return self.anomalia_service.detectar_conluio(votos)
