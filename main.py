# main.py

# Exemplo de uso
from pathlib import Path

from models.classes import Candidato, Partido, Cargo, Eleicao
from processors.classes import SistemaVotacao
from utils.security import KeyManager, CryptographyKeyManager


def run():
    path = Path().parent
    private_key_filename = path / 'resources/private_key.pem'
    cryptography_key_filename = path / 'resources/cryptography_key.pem'
    # Gerando as chaves de criptografia para a demonstração
    KeyManager(private_key_path=private_key_filename.as_posix()).generate_private_key()
    CryptographyKeyManager(key_path=cryptography_key_filename.as_posix()).generate_key()

    # inicializa o sistema de votação
    sistema_votacao = SistemaVotacao(
        chave_privada_path=private_key_filename.as_posix(),
        chave_criptografia_path=cryptography_key_filename.as_posix()
    )

    # Criação dos objetos relacionados aos candidatos
    partido1 = Partido(numero=45, sigla="PA", nome="Partido A")
    partido2 = Partido(numero=65, sigla="PB", nome="Partido B")

    cargo1 = Cargo(id=1, nome="Prefeito", eleicao="Eleição Municipal")
    cargo2 = Cargo(id=2, nome="Vereador", eleicao="Eleição Municipal")

    eleicao = Eleicao(id=1, nome="Eleição Municipal 2024", data="2024-10-06", turnos=1)

    # Votação
    candidato1 = Candidato(
        id=1,
        nome="Candidato 1",
        partido=partido1,
        codigo="45123",
        foto="foto1.jpg",
        cargo=cargo1,
        eleicao=eleicao
    )
    candidato2 = Candidato(
        id=2,
        nome="Candidato 2",
        partido=partido2,
        codigo="65456",
        foto="foto2.jpg",
        cargo=cargo2,
        eleicao=eleicao
    )

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
    print(f"Registro de Urna válido: {registro_urna}")

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


if __name__ == '__main__':
    run()
