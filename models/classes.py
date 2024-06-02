# models/classes.py
from datetime import datetime

from pydantic import BaseModel, Field


class Candidato(BaseModel):
    id: int = Field(..., description="ID único do candidato")
    nome: str = Field(..., description="Nome completo do candidato")
    partido: str = Field(..., description="Partido político do candidato")
    foto: str = Field(..., description="URL da foto do candidato")


class Voto(BaseModel):
    id: int = Field(..., description="ID único do voto")
    candidato: Candidato = Field(..., description="Candidato votado")
    hash_localizacao: str = Field(..., description="Hash de localização do voto na listagem de votos da urna")
    hash_blockchain: str = Field(..., description="Hash do registro do voto no Blockchain")
    qr_code: str = Field(..., description="QR Code contendo todas as informações do voto")


class RegistroImpresso(BaseModel):
    voto: Voto = Field(..., description="Voto registrado")
    data_hora: datetime = Field(..., description="Data e hora da impressão do registro")


class BoletimUrna(BaseModel):
    id: int = Field(..., description="ID único do Boletim de Urna")
    secao: str = Field(..., description="Seção eleitoral")
    zona: str = Field(..., description="Zona eleitoral")
    municipio: str = Field(..., description="Município da urna")
    estado: str = Field(..., description="Estado da urna")
    data_hora: datetime = Field(..., description="Data e hora da geração do Boletim de Urna")
    hash_final_blockchain: str = Field(..., description="Hash final do Blockchain dos votos da urna")
    hash_bu: str = Field(..., description="Hash das informações do Boletim de Urna")
    qr_code: str = Field(..., description="QR Code contendo os hashes e informações do Boletim de Urna")
    votos: list[Voto] = Field(..., description="Lista de votos registrados na urna")
    assinatura: str = Field(None, description="Assinatura digital do Boletim de Urna")


class RegistroUrna(BaseModel):
    id: int = Field(..., description="ID único do Registro de Urna")
    data_hora: datetime = Field(..., description="Data e hora da geração do Registro de Urna")
    boletim_urna_escaneado: bytes = Field(..., description="Boletim de Urna escaneado e assinado pelas autoridades")
    boletim_urna_eletronico: BoletimUrna = Field(..., description="Boletim de Urna eletrônico validado")


class TotalizacaoVotos(BaseModel):
    id: int = Field(..., description="ID único da Totalização de Votos")
    data_hora: datetime = Field(..., description="Data e hora da totalização dos votos")
    votos_totalizados: list[Voto] = Field(..., description="Lista de votos totalizados")
    hash_blockchain: str = Field(..., description="Hash do Blockchain da totalização dos votos")
    assinatura: str = Field(None, description="Assinatura digital da Totalização de Votos")
