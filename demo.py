#!/usr/bin/env python3
"""
Script de demonstração do Sistema de Votação Eletrônica

Este script demonstra o uso programático do sistema de votação,
incluindo geração de chaves, registro de votos, totalização e
geração de boletim de urna.
"""

from datetime import datetime
from pathlib import Path

from core.models.classes import Eleicao, Partido, Cargo, Candidato
from core.processors.classes import SistemaVotacao
from core.utils.security import KeyManager


def main():
    print("=" * 80)
    print("DEMONSTRAÇÃO DO SISTEMA DE VOTAÇÃO ELETRÔNICA")
    print("=" * 80)
    print()

    # 1. Gerar chaves criptográficas
    print("1. Gerando chaves criptográficas...")
    resources_dir = Path("resources")
    resources_dir.mkdir(exist_ok=True)

    private_key_path = resources_dir / "private_key.pem"
    crypto_key_path = resources_dir / "cryptography_key.pem"

    key_manager = KeyManager()
    if not private_key_path.exists():
        key_manager.gerar_chave_privada(str(private_key_path))
        print(f"   ✓ Chave privada gerada: {private_key_path}")
    else:
        print(f"   ✓ Chave privada já existe: {private_key_path}")

    if not crypto_key_path.exists():
        key_manager.gerar_chave_criptografia(str(crypto_key_path))
        print(f"   ✓ Chave de criptografia gerada: {crypto_key_path}")
    else:
        print(f"   ✓ Chave de criptografia já existe: {crypto_key_path}")
    print()

    # 2. Inicializar sistema de votação
    print("2. Inicializando sistema de votação...")
    sistema = SistemaVotacao(str(private_key_path), str(crypto_key_path))
    print("   ✓ Sistema inicializado com sucesso!")
    print()

    # 3. Criar dados de exemplo
    print("3. Criando dados de exemplo...")

    # Partidos
    pt = Partido(numero=13, sigla="PT", nome="Partido dos Trabalhadores")
    psdb = Partido(numero=45, sigla="PSDB", nome="Partido da Social Democracia Brasileira")
    pdt = Partido(numero=12, sigla="PDT", nome="Partido Democrático Trabalhista")

    # Eleição
    eleicao = Eleicao(
        id=1,
        nome="Eleições Municipais 2024",
        data=datetime.now(),
        turnos=2
    )

    # Cargos
    cargo_prefeito = Cargo(id=1, nome="Prefeito", eleicao=1)
    cargo_vereador = Cargo(id=2, nome="Vereador", eleicao=1)

    # Candidatos
    candidatos = [
        Candidato(
            id=1,
            nome="João Silva",
            partido=pt,
            codigo="13",
            foto="https://example.com/joao.jpg",
            cargo=cargo_prefeito,
            eleicao=eleicao
        ),
        Candidato(
            id=2,
            nome="Maria Santos",
            partido=psdb,
            codigo="45",
            foto="https://example.com/maria.jpg",
            cargo=cargo_prefeito,
            eleicao=eleicao
        ),
        Candidato(
            id=3,
            nome="Pedro Oliveira",
            partido=pdt,
            codigo="12",
            foto="https://example.com/pedro.jpg",
            cargo=cargo_prefeito,
            eleicao=eleicao
        ),
    ]

    print(f"   ✓ {len(candidatos)} candidatos criados")
    print()

    # 4. Simular votação
    print("4. Simulando votação...")
    votos_registrados = []

    # Simular 100 votos
    import random
    for i in range(100):
        candidato_escolhido = random.choice(candidatos)
        voto = sistema.votar(candidato_escolhido)
        votos_registrados.append(voto)

        if (i + 1) % 20 == 0:
            print(f"   ✓ {i + 1} votos registrados...")

    print(f"   ✓ Total de {len(votos_registrados)} votos registrados!")
    print()

    # 5. Verificar integridade da blockchain
    print("5. Verificando integridade da blockchain...")
    is_valid = sistema.blockchain.is_chain_valid()
    if is_valid:
        print("   ✓ Blockchain válida! Todos os votos estão íntegros.")
    else:
        print("   ✗ ATENÇÃO: Blockchain inválida! Possível adulteração detectada.")
    print()

    # 6. Totalizar votos
    print("6. Totalizando votos...")
    totalizacao = sistema.totalizar_votos()

    print(f"   Data/Hora: {totalizacao.data_hora}")
    print(f"   Hash Blockchain: {totalizacao.hash_blockchain[:32]}...")
    print(f"   Total de votos únicos: {len(totalizacao.votos_totalizados)}")
    print()

    # Contar votos por candidato
    contagem = {}
    for voto in votos_registrados:
        candidato_id = voto.candidato.id
        if candidato_id not in contagem:
            contagem[candidato_id] = {
                'nome': voto.candidato.nome,
                'partido': voto.candidato.partido.sigla,
                'votos': 0
            }
        contagem[candidato_id]['votos'] += 1

    print("   Resultado da votação:")
    print("   " + "-" * 60)
    print(f"   {'Candidato':<30} {'Partido':<10} {'Votos':>10}")
    print("   " + "-" * 60)

    for dados in sorted(contagem.values(), key=lambda x: x['votos'], reverse=True):
        print(f"   {dados['nome']:<30} {dados['partido']:<10} {dados['votos']:>10}")

    print("   " + "-" * 60)
    print()

    # 7. Gerar Boletim de Urna
    print("7. Gerando Boletim de Urna...")
    boletim = sistema.gerar_boletim_urna()

    print(f"   ID do BU: {boletim.id}")
    print(f"   Seção: {boletim.secao}")
    print(f"   Zona: {boletim.zona}")
    print(f"   Município: {boletim.municipio}")
    print(f"   Estado: {boletim.estado}")
    print(f"   Total de votos: {len(boletim.votos)}")
    print(f"   Hash Final Blockchain: {boletim.hash_final_blockchain[:32]}...")
    print(f"   Assinatura: {'✓ Presente' if boletim.assinatura else '✗ Ausente'}")
    print()

    # 8. Validar Boletim de Urna
    print("8. Validando Boletim de Urna...")
    is_valid_bu = sistema.validar_boletim_urna(boletim)
    if is_valid_bu:
        print("   ✓ Boletim de Urna válido! Assinatura verificada.")
    else:
        print("   ✗ ATENÇÃO: Boletim de Urna inválido!")
    print()

    # 9. Detectar anomalias
    print("9. Detectando anomalias nos votos...")
    anomalias = sistema.detectar_anomalias(votos_registrados)
    print(f"   Total de anomalias detectadas: {len(anomalias)}")

    if len(anomalias) > 0:
        print("   ⚠️  Votos anômalos encontrados (podem indicar problemas):")
        for voto_anomalo in anomalias[:5]:  # Mostrar apenas os primeiros 5
            print(f"      - Voto ID: {voto_anomalo.id}, Candidato: {voto_anomalo.candidato.nome}")
    else:
        print("   ✓ Nenhuma anomalia significativa detectada.")
    print()

    # 10. Estatísticas finais
    print("=" * 80)
    print("ESTATÍSTICAS FINAIS")
    print("=" * 80)
    print(f"Total de votos registrados: {len(votos_registrados)}")
    print(f"Total de blocos na blockchain: {len(sistema.blockchain.chain)}")
    print(f"Integridade da blockchain: {'✓ Válida' if is_valid else '✗ Inválida'}")
    print(f"Assinatura do BU: {'✓ Válida' if is_valid_bu else '✗ Inválida'}")
    print(f"Anomalias detectadas: {len(anomalias)}")
    print()

    # 11. Logs de auditoria
    print("Logs de auditoria salvos em: security/audit_*.log")
    print()

    print("=" * 80)
    print("DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemonstração interrompida pelo usuário.")
    except Exception as e:
        print(f"\n\nERRO: {e}")
        import traceback
        traceback.print_exc()
