# Documento de Análise de Requisitos para Urna Eletrônica

## 1. Introdução
Este documento descreve os requisitos para o desenvolvimento de uma urna eletrônica utilizando a linguagem de programação Python e o framework FastAPI. A urna eletrônica deve permitir o upload de arquivos de chave criptográfica, o cadastramento de dados de eleições, partidos, cargos e candidatos, além de funcionalidades adicionais como a impressão do voto.

## 2. Objetivos
- Desenvolver uma urna eletrônica segura e eficiente.
- Permitir o upload de arquivos de chave criptográfica.
- Cadastrar e gerenciar dados de eleições, partidos, cargos e candidatos.
- Implementar funcionalidades adicionais, incluindo a impressão do voto.

## 3. Requisitos Funcionais

### 3.1 Upload de Arquivos de Chave
- **RF01**: A urna deve permitir o upload de dois arquivos de chave: `cryptography_key.pem` e `private_key.pem`.
- **RF02**: Os arquivos de chave devem ser enviados para um servidor desenvolvido em FastAPI.

### 3.2 Cadastro de Dados
- **RF03**: A urna deve permitir o cadastramento dos dados da eleição utilizando a classe `Eleicao`.
- **RF04**: A urna deve permitir o cadastramento de partidos utilizando a classe `Partido`.
- **RF05**: A urna deve permitir o cadastramento de cargos utilizando a classe `Cargo`.
- **RF06**: A urna deve permitir o cadastramento de candidatos utilizando a classe `Candidato`.

### 3.3 Funcionalidades Adicionais
- **RF07**: A urna deve permitir a impressão do voto após a confirmação do eleitor.
- **RF08**: A urna deve garantir a segurança e integridade dos dados utilizando criptografia.
- **RF09**: A urna deve permitir a visualização dos dados cadastrados de eleições, partidos, cargos e candidatos.
- **RF10**: A urna deve permitir a votação eletrônica com interface amigável para o eleitor.

## 4. Requisitos Não Funcionais

### 4.1 Desempenho
- **RNF01**: A urna deve processar o upload de arquivos de chave e o cadastramento de dados de forma eficiente, sem atrasos perceptíveis para o usuário.

### 4.2 Segurança
- **RNF02**: A urna deve utilizar criptografia para garantir a segurança dos dados.
- **RNF03**: A urna deve implementar autenticação e autorização para acesso aos dados e funcionalidades.

### 4.3 Usabilidade
- **RNF04**: A interface da urna deve ser intuitiva e fácil de usar para eleitores de todas as idades.

### 4.4 Confiabilidade
- **RNF05**: A urna deve ser robusta e confiável, garantindo a integridade dos votos e dados cadastrados.

## 5. Modelos de Dados

### 5.1 Eleicao
```python
from pydantic import BaseModel, Field
from datetime import datetime

class Eleicao(BaseModel):
    id: int = Field(..., description="ID único da eleição")
    nome: str = Field(..., description="Nome da eleição")
    data: datetime = Field(..., description="Data da eleição")
    turnos: int = Field(..., description="Número de turnos da eleição (1 ou 2)")
```

### 5.2 Partido
```python
from pydantic import BaseModel, Field

class Partido(BaseModel):
    numero: int = Field(..., description="Número do partido")
    sigla: str = Field(..., description="Sigla do partido")
    nome: str = Field(..., description="Nome completo do partido")
```

### 5.3 Cargo
```python
from pydantic import BaseModel, Field

class Cargo(BaseModel):
    id: int = Field(..., description="ID único do cargo")
    nome: str = Field(..., description="Nome do cargo")
    eleicao: str = Field(..., description="Eleição a qual o cargo pertence")
```

### 5.4 Candidato
```python
from pydantic import BaseModel, Field

class Candidato(BaseModel):
    id: int = Field(..., description="ID único do candidato")
    nome: str = Field(..., description="Nome completo do candidato")
    partido: Partido = Field(..., description="Partido político do candidato")
    codigo: str = Field(..., description="Código do candidato (prefixo do partido + código específico)")
    foto: str = Field(..., description="URL da foto do candidato")
    cargo: Cargo = Field(..., description="Cargo ao qual o candidato está concorrendo")
    eleicao: Eleicao = Field(..., description="Eleição da qual o candidato está participando")
```

## 6. Funcionalidades da Urna Brasileira com Impressão do Voto

### 6.1 Processo de Votação
- **F01**: O eleitor deve ser autenticado antes de iniciar o processo de votação.
- **F02**: O eleitor deve selecionar os candidatos para os cargos disponíveis.
- **F03**: Após a seleção, o eleitor deve confirmar o voto.
- **F04**: Após a confirmação, a urna deve imprimir um comprovante do voto.

### 6.2 Segurança e Integridade
- **F05**: Utilizar criptografia para proteger os dados dos votos.
- **F06**: Implementar logs de auditoria para rastrear todas as ações realizadas na urna.

### 6.3 Interface do Usuário
- **F07**: A interface deve ser clara e intuitiva, guiando o eleitor durante todo o processo de votação.
- **F08**: Exibir informações claras sobre os candidatos e cargos durante a votação.

## 7. Conclusão

Este documento de análise de requisitos detalha as funcionalidades e características necessárias para o desenvolvimento
de uma urna eletrônica segura e eficiente. A implementação deve seguir os requisitos funcionais e não funcionais
descritos, garantindo uma experiência de votação confiável e segura para os eleitores.