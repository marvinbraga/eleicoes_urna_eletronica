# Sistema de Votação Eletrônica

## Visão Geral

Sistema de votação eletrônica desenvolvido em Python que utiliza blockchain para garantir a integridade dos votos. O projeto implementa um fluxo completo de eleição desde o registro de votos até a totalização, incluindo validação por meio de registros impressos com QR Codes.

## Arquitetura do Projeto

O projeto está organizado em:

- **core/**: Núcleo do sistema
  - **blockchain/**: Implementação da tecnologia blockchain para votos
  - **models/**: Modelos de dados (Candidato, Partido, Cargo, Eleição, Voto, etc.)
  - **processors/**: Lógica de processamento do sistema de votação
  - **utils/**: Utilitários (segurança, datetime, geração de QR codes)

- **backend/**: API REST em FastAPI
  - Endpoints para upload de dados da eleição
  - Gerenciamento de votos
  - Consulta de candidatos por cargo
  - Totalização de votos

- **resources/**: Arquivos de recursos (chaves criptográficas, dados de eleição)

## Stack Tecnológica

### Backend
- **Python 3.15**
- **FastAPI**: Framework web moderno e rápido
- **Pydantic**: Validação de dados
- **Redis**: Armazenamento em cache e dados de sessão
- **Jinja2**: Templates HTML

### Segurança
- **cryptography**: Criptografia de dados
- **Blockchain**: Integridade dos votos

### Processamento
- **scikit-learn**: Detecção de anomalias e conluio
- **Pillow + pyzbar**: Processamento de QR Codes
- **qrcode**: Geração de QR Codes

### Desenvolvimento
- **uv**: Gerenciador de dependências
- **pytest**: Testes
- **flake8**: Linting
- **coverage/pytest-cov**: Cobertura de testes
- **loguru**: Logging

## Dependências Principais

```toml
requires-python = ">=3.15"
fastapi = "^0.111.0"
pydantic = "^2.7.2"
cryptography = "^42.0.7"
redis = "^5.0.4"
qrcode = "^7.4.2"
scikit-learn = "^1.5.0"
loguru = "^0.7.2"
```

## Comandos Úteis

### Instalação
```bash
uv sync
```

### Executar o sistema (exemplo standalone)
```bash
uv run python core/main.py
```

### Executar o backend
```bash
uv run uvicorn backend.app:app --host 0.0.0.0 --port 7000 --reload
```

### Executar testes
```bash
uv run pytest
```

### Cobertura de testes
```bash
uv run pytest --cov=core --cov=backend --cov-report=html
```

### Linting
```bash
uv run flake8 core/ backend/
```

### Docker
```bash
docker-compose up -d
```

## Fluxo de Trabalho

### 1. Votação
- Eleitor seleciona candidato na urna
- Sistema gera registro de voto usando blockchain
- Registro impresso é gerado com QR Code
- Voto é confirmado e armazenado anonimamente

### 2. Validação dos Votos
- Fiscais podem fazer escrutínio público usando registros impressos
- Sistema lê QR Codes para validar votos
- Conferência entre registros eletrônicos e impressos

### 3. Boletim de Urna (BU)
- Totalização dos votos da urna
- Geração de BU com hash final do blockchain
- Impressão com QR Code

### 4. Validação do BU
- Conferência do BU salvo vs impresso
- Assinaturas das autoridades

### 5. Registro de Urna
- Escaneamento do BU assinado
- Criptografia e compactação
- Armazenamento seguro

### 6. Totalização
- Processamento usando blockchain
- Detecção de anomalias
- Detecção de conluio
- Verificação de integridade

## Estrutura de Dados

### Modelos Principais
- **Partido**: Número, sigla, nome
- **Cargo**: ID, nome, eleição
- **Eleicao**: ID, nome, data, turnos
- **Candidato**: ID, nome, partido, código, foto, cargo, eleição
- **Voto**: ID, candidato, hash_localizacao, hash_blockchain, qr_code, data_hora
- **BoletimUrna**: Informações da seção, votos, hashes, assinatura
- **TotalizacaoVotos**: Votos totalizados, hash blockchain, assinatura

## Segurança

O sistema implementa múltiplas camadas de segurança:

1. **Blockchain**: Imutabilidade dos votos
2. **Criptografia**: Chaves RSA e criptografia simétrica
3. **Hashes**: Verificação de integridade em cada etapa
4. **QR Codes**: Auditoria física dos registros
5. **Anonimização**: Desvinculação do voto do eleitor
6. **Detecção de Anomalias**: Machine learning para identificar padrões suspeitos

## Padrões de Código

- Use Pydantic para validação de dados
- Siga PEP 8 para estilo de código
- Docstrings em português
- Type hints em todas as funções
- Testes unitários para funcionalidades críticas

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
BACKEND_URL=http://localhost:7000
REDIS_HOST=localhost
REDIS_PORT=9379
```

## Notas Importantes

- As chaves criptográficas são geradas automaticamente no primeiro uso
- O Redis deve estar em execução para o backend funcionar
- Os dados da eleição são carregados via upload de JSON
- O sistema suporta múltiplos cargos e candidatos por eleição

## Licença

GNU General Public License v3.0

## Autor

Marcus Vinicius Braga (mvbraga@gmail.com)
