"""
Enums para estados e status utilizados no sistema de votação eletrônica.
"""
from enum import Enum


class EstadoBrasil(str, Enum):
    """
    Estados do Brasil.
    """
    AC = "Acre"
    AL = "Alagoas"
    AP = "Amapá"
    AM = "Amazonas"
    BA = "Bahia"
    CE = "Ceará"
    DF = "Distrito Federal"
    ES = "Espírito Santo"
    GO = "Goiás"
    MA = "Maranhão"
    MT = "Mato Grosso"
    MS = "Mato Grosso do Sul"
    MG = "Minas Gerais"
    PA = "Pará"
    PB = "Paraíba"
    PR = "Paraná"
    PE = "Pernambuco"
    PI = "Piauí"
    RJ = "Rio de Janeiro"
    RN = "Rio Grande do Norte"
    RS = "Rio Grande do Sul"
    RO = "Rondônia"
    RR = "Roraima"
    SC = "Santa Catarina"
    SP = "São Paulo"
    SE = "Sergipe"
    TO = "Tocantins"


class StatusVoto(str, Enum):
    """
    Status de um voto no sistema.
    """
    PENDENTE = "pendente"
    REGISTRADO = "registrado"
    VALIDADO = "validado"
    INVALIDADO = "invalidado"
    DUPLICADO = "duplicado"


class TipoLog(str, Enum):
    """
    Tipos de log de auditoria.
    """
    VOTO_REGISTRADO = "voto_registrado"
    VOTO_VALIDADO = "voto_validado"
    VOTO_INVALIDADO = "voto_invalidado"
    VOTO_DUPLICADO = "voto_duplicado"
    BOLETIM_GERADO = "boletim_gerado"
    TOTALIZACAO_CONCLUIDA = "totalizacao_concluida"
    ANOMALIA_DETECTADA = "anomalia_detectada"
    CONLUIO_DETECTADO = "conluio_detectado"
    ERRO_SISTEMA = "erro_sistema"


class TipoTransacao(str, Enum):
    """
    Tipos de transação na blockchain.
    """
    VOTO = "voto"
    BOLETIM_URNA = "boletim_urna"
    TOTALIZACAO = "totalizacao"
    AUDITORIA = "auditoria"
