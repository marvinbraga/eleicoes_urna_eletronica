# Sistema de Votação Eletrônica (Urna Eletrônica)

Sistema de votação eletrônica desenvolvido em Python com FastAPI, implementando segurança criptográfica, blockchain e geração de QR codes para auditoria de votos.

## 🚀 Funcionalidades Implementadas

### ✅ Sistema de Votação
- ✓ Registro de votos com criptografia RSA e Fernet
- ✓ Geração automática de QR Code para cada voto
- ✓ Armazenamento em blockchain para garantir integridade
- ✓ Sistema de nonce para prevenir duplicação de votos
- ✓ Auditoria completa com logs timestamped

### ✅ Interface Web
- ✓ Upload de chaves de segurança e dados da eleição
- ✓ Seleção de cargo
- ✓ Busca de candidatos por código com autocomplete
- ✓ Confirmação de voto com visualização de candidato
- ✓ Recibo de voto com QR Code
- ✓ Totalização de votos em tempo real
- ✓ Geração de Boletim de Urna

### ✅ Segurança
- ✓ Criptografia RSA 2048-bit
- ✓ Criptografia simétrica Fernet
- ✓ Assinaturas digitais HMAC-PSS
- ✓ Hash SHA-256 para integridade
- ✓ Blockchain para imutabilidade
- ✓ Logs de auditoria

### ✅ API REST
- ✓ `POST /upload-keys` - Upload de chaves e dados da eleição
- ✓ `GET /keys-status` - Verificar status das chaves
- ✓ `GET /cargos/{eleicao_id}` - Listar cargos
- ✓ `GET /candidatos/{cargo_id}` - Listar candidatos por cargo
- ✓ `GET /buscar-candidatos/{cargo_id}/{codigo}` - Buscar candidatos por código
- ✓ `POST /votar` - Registrar voto
- ✓ `POST /verificar-voto` - Verificar voto via QR code
- ✓ `GET /totalizar-votos/{eleicao_id}` - Totalizar votos
- ✓ `GET /gerar-boletim-urna` - Gerar Boletim de Urna

## 📋 Pré-requisitos

- Python 3.10+
- Poetry (gerenciador de dependências)
- Redis (para armazenamento em cache)
- Docker e Docker Compose (opcional)

## 🔧 Instalação

### 1. Clonar o repositório

```bash
git clone <repository-url>
cd eleicoes_urna_eletronica
```

### 2. Instalar dependências

```bash
poetry install
```

### 3. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
BACKEND_URL=http://localhost:7000
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 4. Iniciar Redis

Com Docker:
```bash
docker-compose up -d redis
```

Ou manualmente:
```bash
redis-server
```

## 🎮 Uso

### Iniciar o servidor

```bash
poetry run uvicorn backend.app:app --host 0.0.0.0 --port 7000 --reload
```

### Acessar a interface web

Abra o navegador em: `http://localhost:7000`

### Fluxo de uso

1. **Upload de Chaves e Dados**
   - Faça upload da chave de criptografia (`.pem`)
   - Faça upload da chave privada (`.pem`)
   - Faça upload do arquivo JSON da eleição

2. **Votação**
   - Selecione o cargo
   - Digite o código do candidato
   - Clique no candidato desejado
   - Confirme o voto
   - Visualize o recibo com QR Code

3. **Administração**
   - Clique em "Totalizar Votos" para ver os resultados
   - Clique em "Gerar Boletim" para criar o Boletim de Urna

## 🧪 Testes

### Executar todos os testes

```bash
poetry run pytest tests/ -v
```

### Executar testes específicos

```bash
poetry run pytest tests/test_voting_system.py -v
```

### Executar testes com cobertura

```bash
poetry run pytest tests/ --cov=core --cov=backend --cov-report=html
```

## 📁 Estrutura do Projeto

```
eleicoes_urna_eletronica/
├── backend/
│   ├── app.py              # API FastAPI
│   ├── templates/
│   │   └── index.html      # Interface web
│   └── static/
│       ├── scripts.js      # JavaScript frontend
│       └── styles.css      # Estilos
├── core/
│   ├── blockchain/
│   │   └── classes.py      # Implementação blockchain
│   ├── models/
│   │   ├── classes.py      # Modelos de dados
│   │   └── partidos.py     # Partidos políticos
│   ├── processors/
│   │   └── classes.py      # Serviços do sistema
│   └── utils/
│       ├── security.py     # Gerenciamento de chaves
│       ├── qr_code_gen.py  # Geração de QR codes
│       └── datetime.py     # Utilitários de data/hora
├── tests/
│   ├── test_voting_system.py  # Testes do sistema
│   └── test_api.py             # Testes da API
├── resources/
│   └── eleicao.json        # Dados de exemplo
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## 🔐 Segurança

### Geração de Chaves

Para gerar novas chaves criptográficas:

```python
from core.utils.security import KeyManager

key_manager = KeyManager()
key_manager.gerar_chave_privada("private_key.pem")
key_manager.gerar_chave_criptografia("cryptography_key.pem")
```

### Boas Práticas

- ⚠️ Nunca commite chaves privadas no Git
- ⚠️ Use HTTPS em produção
- ⚠️ Implemente autenticação de eleitores
- ⚠️ Configure Redis com senha
- ⚠️ Use HSM para armazenamento de chaves em produção

## 📊 Exemplo de Dados de Eleição

```json
{
  "eleicao": {
    "id": 1,
    "nome": "Eleições Municipais 2024",
    "data": "2024-10-06T00:00:00",
    "turnos": 2
  },
  "partidos": [
    {
      "numero": 13,
      "sigla": "PT",
      "nome": "Partido dos Trabalhadores"
    }
  ],
  "cargos": [
    {
      "id": 1,
      "nome": "Prefeito",
      "eleicao": 1
    }
  ],
  "candidatos": [
    {
      "id": 1,
      "nome": "João da Silva",
      "partido": {...},
      "codigo": "13",
      "foto": "https://example.com/foto.jpg",
      "cargo": {...},
      "eleicao": {...}
    }
  ]
}
```

## 🐛 Solução de Problemas

### Redis não está rodando

```bash
# Verificar se Redis está rodando
redis-cli ping

# Se retornar "PONG", está funcionando
# Caso contrário, inicie o Redis:
redis-server
```

### Erro ao importar módulos

```bash
# Certifique-se de estar usando o ambiente virtual Poetry
poetry shell

# Reinstale as dependências
poetry install
```

### Porta 7000 já em uso

```bash
# Mudar a porta no arquivo .env
BACKEND_URL=http://localhost:8000

# E ao iniciar o servidor:
poetry run uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

## 📝 TODO / Melhorias Futuras

- [ ] Implementar autenticação de eleitores
- [ ] Adicionar suporte para múltiplos turnos
- [ ] Implementar detecção de anomalias em tempo real
- [ ] Criar dashboard de administração completo
- [ ] Adicionar suporte para votos nulos e brancos
- [ ] Implementar impressão física de recibos
- [ ] Adicionar scanner de QR code para validação
- [ ] Implementar backup automático de votos
- [ ] Adicionar suporte para eleições simultâneas
- [ ] Criar relatórios de auditoria detalhados

## 👥 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto é desenvolvido para fins educacionais e de demonstração.

## 🙏 Agradecimentos

- FastAPI por fornecer um framework web moderno e rápido
- Cryptography library por implementações seguras de criptografia
- Redis por armazenamento em cache eficiente
- Bootstrap por componentes UI responsivos

## 📞 Suporte

Para questões e suporte, abra uma issue no GitHub.

---

Desenvolvido com ❤️ para garantir eleições seguras e transparentes.
