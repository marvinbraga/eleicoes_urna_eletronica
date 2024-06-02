# processors/classes.py
import base64
import json
import os
from datetime import datetime
from pathlib import Path
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


class SistemaVotacao:
    def __init__(self, chave_privada_path: str, chave_criptografia_path: str):
        self.blockchain = Blockchain()
        self.votos: List[Voto] = []
        self.boletins_urna: List[BoletimUrna] = []

        # Carrega a chave de criptografia a partir do arquivo, se existir
        if os.path.exists(chave_criptografia_path):
            with open(chave_criptografia_path, 'rb') as file:
                self.chave_criptografia = file.read()

        self.cifra = Fernet(self.chave_criptografia)

        # Carrega a chave privada a partir do arquivo
        with open(chave_privada_path, 'rb') as file:
            self.chave_privada = serialization.load_pem_private_key(
                file.read(),
                password=None
            )

        self.chave_publica = self.chave_privada.public_key()

    def criptografar_dados(self, dados: str) -> str:
        dados_criptografados = self.cifra.encrypt(dados.encode())
        return base64.b64encode(dados_criptografados).decode()

    def descriptografar_dados(self, dados_criptografados: str) -> str:
        dados_criptografados_bytes = base64.b64decode(dados_criptografados)
        return self.cifra.decrypt(dados_criptografados_bytes).decode()

    def assinar_dados(self, dados: str) -> bytes:
        assinatura = self.chave_privada.sign(
            dados.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return assinatura

    def verificar_assinatura(self, dados: str, assinatura: bytes) -> bool:
        try:
            self.chave_publica.verify(
                assinatura,
                dados.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            return False

    def votar(self, candidato: Candidato) -> Voto:
        voto = Voto(
            id=len(self.votos) + 1,
            candidato=candidato,
            hash_localizacao=self.blockchain.chain[-1].hash,
            hash_blockchain=self.blockchain.chain[-1].hash,
            qr_code=f"qrcode_{len(self.votos) + 1}"
        )
        voto_json = voto.json()
        assinatura = self.assinar_dados(voto_json)
        voto_assinado = {
            "voto": voto_json,
            "assinatura": base64.b64encode(assinatura).decode()
        }
        voto_criptografado = self.criptografar_dados(json.dumps(voto_assinado))
        self.votos.append(voto)
        self.blockchain.add_transaction(voto_criptografado)
        self.blockchain.mine_pending_transactions()
        return voto

    def gerar_registro_impresso(self, voto: Voto) -> RegistroImpresso:
        return RegistroImpresso(
            voto=voto,
            data_hora=datetime.now()
        )

    def validar_votos(self, registros_impressos: List[RegistroImpresso]) -> bool:
        for registro in registros_impressos:
            voto = next((v for v in self.votos if v.id == registro.voto.id), None)
            if voto is None or voto.dict() != registro.voto.dict():
                return False
        return True

    def gerar_boletim_urna(self) -> BoletimUrna:
        boletim = BoletimUrna(
            id=len(self.boletins_urna) + 1,
            secao="Seção XYZ",
            zona="Zona 123",
            municipio="Município ABC",
            estado="Estado MN",
            data_hora=datetime.now(),
            hash_final_blockchain=self.blockchain.chain[-1].hash,
            hash_bu=self.blockchain.chain[-1].hash,
            qr_code=f"qrcode_bu_{len(self.boletins_urna) + 1}",
            votos=self.votos
        )

        # Gera a assinatura digital do boletim de urna
        boletim_dict = boletim.dict(exclude_none=True)
        assinatura_boletim = self.assinar_dados(json.dumps(boletim_dict, default=datetime_to_string, sort_keys=True))

        # Adiciona a assinatura ao boletim de urna
        boletim.assinatura = base64.b64encode(assinatura_boletim).decode()

        boletim_criptografado = self.criptografar_dados(boletim.json())
        self.boletins_urna.append(boletim)
        return boletim

    def validar_boletim_urna(self, boletim_impresso: BoletimUrna) -> bool:
        boletim_eletronico = next((b for b in self.boletins_urna if b.id == boletim_impresso.id), None)

        if boletim_eletronico is None:
            return False

        # Verifica a assinatura do boletim de urna
        boletim_dict = boletim_eletronico.dict(exclude_none=True, exclude={'assinatura'})
        assinatura_boletim = base64.b64decode(boletim_eletronico.assinatura)
        return self.verificar_assinatura(
            json.dumps(boletim_dict, default=datetime_to_string, sort_keys=True),
            assinatura_boletim
        )

    def gerar_registro_urna(self, boletim_urna: BoletimUrna) -> RegistroUrna:
        return RegistroUrna(
            id=len(self.boletins_urna),
            data_hora=datetime.now(),
            boletim_urna_escaneado=b"dados_escaneados",
            boletim_urna_eletronico=boletim_urna
        )

    def totalizar_votos(self) -> TotalizacaoVotos:
        tally = {}
        for block in self.blockchain.chain:
            for transaction in block.transactions:
                voto_descriptografado = self.descriptografar_dados(transaction)
                voto_assinado = json.loads(voto_descriptografado)
                voto_json = voto_assinado["voto"]
                assinatura = base64.b64decode(voto_assinado["assinatura"])

                if self.verificar_assinatura(voto_json, assinatura):
                    voto = Voto.parse_raw(voto_json)
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
                else:
                    print("Voto inválido: assinatura não confere")

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

        totalizacao = TotalizacaoVotos(
            id=1,
            data_hora=datetime.now(),
            votos_totalizados=votos_totalizados,
            hash_blockchain=self.blockchain.chain[-1].hash
        )

        # Gera a assinatura digital do resultado da totalização
        totalizacao_dict = totalizacao.dict(exclude_none=True)
        assinatura_totalizacao = self.assinar_dados(
            json.dumps(totalizacao_dict, default=datetime_to_string, sort_keys=True))
        # Adiciona a assinatura à totalização
        totalizacao.assinatura = base64.b64encode(assinatura_totalizacao).decode()

        return totalizacao

    def verificar_integridade_totalizacao(self, totalizacao: TotalizacaoVotos) -> bool:
        # Verifica a assinatura da totalização
        totalizacao_dict = totalizacao.dict(exclude_none=True, exclude={'assinatura'})
        assinatura_totalizacao = base64.b64decode(totalizacao.assinatura)
        return self.verificar_assinatura(
            json.dumps(totalizacao_dict, default=datetime_to_string, sort_keys=True),
            assinatura_totalizacao,
        )

    def _extrair_caracteristicas(self, voto):
        # Extrai características numéricas do voto
        candidato_id = voto.candidato.id
        hash_localizacao = hash(voto.hash_localizacao) % 1000000
        hash_blockchain = hash(voto.hash_blockchain) % 1000000
        return [candidato_id, hash_localizacao, hash_blockchain]

    def detectar_anomalias(self, votos):
        # Extrai as características numéricas dos votos
        caracteristicas = [self._extrair_caracteristicas(voto) for voto in votos]

        # Cria uma instância do IsolationForest
        isolation_forest = IsolationForest(n_estimators=100, contamination=0.1)

        # Treina o modelo com as características dos votos
        isolation_forest.fit(caracteristicas)

        # Obtém as pontuações de anomalia para cada voto
        anomaly_scores = isolation_forest.decision_function(caracteristicas)

        # Identifica os votos anômalos com base nas pontuações
        anomalias = [voto for voto, score in zip(votos, anomaly_scores) if score < 0]

        return anomalias

    def detectar_conluio(self, votos):
        # Extrai as características numéricas dos votos
        caracteristicas = [self._extrair_caracteristicas(voto) for voto in votos]

        # Cria uma instância do IsolationForest
        isolation_forest = IsolationForest(n_estimators=100, contamination=0.1)

        # Treina o modelo com as características dos votos
        isolation_forest.fit(caracteristicas)

        # Obtém as pontuações de anomalia para cada voto
        anomaly_scores = isolation_forest.decision_function(caracteristicas)

        # Identifica os votos suspeitos de conluio com base nas pontuações
        conluio_suspeito = [voto for voto, score in zip(votos, anomaly_scores) if score < -0.5]

        return conluio_suspeito


def processar_votos(self, votos: List[Voto]):
    for voto_criptografado in votos:
        voto_descriptografado = self.descriptografar_dados(voto_criptografado)
        voto_assinado = json.loads(voto_descriptografado)
        voto_json = voto_assinado["voto"]
        assinatura = base64.b64decode(voto_assinado["assinatura"])

        if self.verificar_assinatura(voto_json, assinatura):
            voto = Voto.parse_raw(voto_json)
            self.votos.append(voto)
            self.blockchain.add_transaction(voto_criptografado)
        else:
            print("Voto inválido: assinatura não confere")

    self.blockchain.mine_pending_transactions()


if __name__ == '__main__':
    # Exemplo de uso

    path = Path(__file__).parent.parent
    private_key_filename = path / 'resources/private_key.pem'
    # Exemplo de uso
    cryptography_key_filename = path / 'resources/cryptography_key.pem'

    sistema_votacao = SistemaVotacao(
        chave_privada_path=private_key_filename.as_posix(),
        chave_criptografia_path=cryptography_key_filename.as_posix()
    )

    # Votação
    candidato1 = Candidato(id=1, nome="Candidato 1", partido="Partido A", foto="foto1.jpg")
    candidato2 = Candidato(id=2, nome="Candidato 2", partido="Partido B", foto="foto2.jpg")

    voto1 = sistema_votacao.votar(candidato1)
    voto2 = sistema_votacao.votar(candidato2)

    registro_impresso1 = sistema_votacao.gerar_registro_impresso(voto1)
    registro_impresso2 = sistema_votacao.gerar_registro_impresso(voto2)

    # Validação dos votos
    registros_impressos = [registro_impresso1, registro_impresso2]
    votos_validos = sistema_votacao.validar_votos(registros_impressos)
    print(f"Votos válidos: {votos_validos}")

    # Criação do Boletim de Urna
    boletim_urna = sistema_votacao.gerar_boletim_urna()

    # Validação do Boletim de Urna
    boletim_valido = sistema_votacao.validar_boletim_urna(boletim_urna)
    print(f"Boletim de Urna válido: {boletim_valido}")

    # Criação do Registro de Urna
    registro_urna = sistema_votacao.gerar_registro_urna(boletim_urna)

    # Totalização dos votos
    totalizacao = sistema_votacao.totalizar_votos()
    print(f"Totalização dos votos: {totalizacao}")
    for voto in totalizacao.votos_totalizados:
        print(voto)

    # Verifica integridade da totalização
    eh_integra_totalizacao = sistema_votacao.verificar_integridade_totalizacao(totalizacao)
    print(f"Integridade da totalização de votos: {eh_integra_totalizacao}")

    # Detecção de anomalias após a totalização
    votos_totalizados = totalizacao.votos_totalizados
    anomalias = sistema_votacao.detectar_anomalias(votos_totalizados)
    print(f"Anomalias detectadas após a totalização: {anomalias}")

    # Detecção de conluio após a totalização
    conluio_suspeito = sistema_votacao.detectar_conluio(votos_totalizados)
    print(f"Votos suspeitos de conluio após a totalização: {conluio_suspeito}")
