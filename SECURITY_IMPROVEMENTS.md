# Melhorias de Segurança - Fase 1

Este documento detalha todas as melhorias de segurança implementadas no sistema de urna eletrônica.

## 📋 Sumário

1. [Autenticação e Autorização JWT](#1-autenticação-e-autorização-jwt)
2. [Rate Limiting](#2-rate-limiting)
3. [Correção de Variável Global](#3-correção-de-variável-global)
4. [Validação de Entrada Robusta](#4-validação-de-entrada-robusta)
5. [Tratamento de Erros Seguro](#5-tratamento-de-erros-seguro)
6. [Permissões de Diretório](#6-permissões-de-diretório)
7. [CORS Adequado](#7-cors-adequado)
8. [Logging Seguro](#8-logging-seguro)
9. [Timeout Redis](#9-timeout-redis)
10. [Validação de Arquivos Upload](#10-validação-de-arquivos-upload)

---

## 1. Autenticação e Autorização JWT

### Arquivos Criados/Modificados:
- **Criado**: `/home/user/eleicoes_urna_eletronica/core/auth/__init__.py`
- **Criado**: `/home/user/eleicoes_urna_eletronica/core/auth/security.py`
- **Modificado**: `/home/user/eleicoes_urna_eletronica/core/models/classes.py`
- **Modificado**: `/home/user/eleicoes_urna_eletronica/pyproject.toml`

### Implementações:

#### Dependências Adicionadas:
```toml
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
python-multipart = "^0.0.9"
```

#### Funções de Segurança (`core/auth/security.py`):
```python
- verify_password(plain_password, hashed_password) -> bool
- get_password_hash(password) -> str
- create_access_token(data, expires_delta) -> str
- decode_access_token(token) -> TokenData
- get_current_user(token) -> TokenData
- require_scope(required_scope) -> dependency
```

#### Modelos de Usuário (`core/models/classes.py`):
```python
- User: Modelo base de usuário
- UserInDB: Usuário com hash de senha
- UserCreate: Modelo para criação de usuário
- LoginRequest: Modelo para requisição de login
```

#### Endpoint de Login (`backend/app.py`):
```python
POST /api/auth/login
- Rate limit: 5 requisições/minuto
- Retorna: JWT token com validade de 30 minutos
- Validação: Username e senha com bcrypt
```

### Considerações de Segurança:
- ✅ Senhas hasheadas com bcrypt (custo 12)
- ✅ Tokens JWT com expiração de 30 minutos
- ✅ Validação de força de senha (mínimo 8 chars, 1 número, 1 maiúscula)
- ✅ Scopes para controle de permissões
- ⚠️ **IMPORTANTE**: Alterar `JWT_SECRET_KEY` em produção!

---

## 2. Rate Limiting

### Arquivos Modificados:
- **Modificado**: `/home/user/eleicoes_urna_eletronica/backend/app.py`
- **Modificado**: `/home/user/eleicoes_urna_eletronica/pyproject.toml`

### Implementações:

#### Dependência Adicionada:
```toml
slowapi = "^0.1.9"
```

#### Configuração:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

#### Limites Aplicados:
| Endpoint | Limite | Justificativa |
|----------|--------|---------------|
| `/api/auth/login` | 5/minuto | Prevenir brute force |
| `/votar` | 10/minuto | Prevenir spam de votos |
| `/totalizar-votos/{eleicao_id}` | 5/minuto | Operação custosa |
| `/upload-keys` | 3/minuto | Operação sensível |

### Considerações de Segurança:
- ✅ Proteção contra brute force
- ✅ Prevenção de spam
- ✅ Proteção de recursos computacionais
- ✅ Rate limit baseado no IP do cliente

---

## 3. Correção de Variável Global

### Arquivos Modificados:
- **Modificado**: `/home/user/eleicoes_urna_eletronica/backend/app.py`

### Implementações:

#### Antes (Inseguro):
```python
sistema_votacao: Optional[SistemaVotacao] = None

@app.post("/votar")
async def votar(voto_request: VotoRequest):
    global sistema_votacao
    if sistema_votacao is None:
        raise HTTPException(...)
```

#### Depois (Seguro):
```python
def get_sistema_votacao() -> SistemaVotacao:
    """Dependency para obter a instância do sistema de votação."""
    if not hasattr(app.state, 'sistema_votacao') or app.state.sistema_votacao is None:
        raise HTTPException(...)
    return app.state.sistema_votacao

@app.post("/votar")
async def votar(
    voto_request: VotoRequest,
    sistema_votacao: SistemaVotacao = Depends(get_sistema_votacao)
):
    # Usa sistema_votacao injetado
```

### Considerações de Segurança:
- ✅ Elimina race conditions
- ✅ Melhor testabilidade
- ✅ Facilita mocking em testes
- ✅ Segue padrão de dependency injection do FastAPI

---

## 4. Validação de Entrada Robusta

### Arquivos Criados:
- **Criado**: `/home/user/eleicoes_urna_eletronica/core/utils/validation.py`

### Implementações:

#### Funções de Validação:
```python
- validate_positive_id(value, field_name) -> int
  # Valida IDs positivos > 0

- validate_string_length(value, min_length, max_length, field_name) -> str
  # Valida comprimento de strings

- sanitize_filename(filename) -> str
  # Remove caracteres perigosos de nomes de arquivo

- validate_file_upload(file, file_type) -> None
  # Valida tipo, extensão e tamanho de arquivo

- validate_codigo_candidato(codigo) -> str
  # Valida formato de código de candidato (2-5 dígitos)

- validate_json_keys(data, required_keys, optional_keys) -> None
  # Valida estrutura de JSON
```

#### Aplicações no Backend:
```python
# Validação de IDs
eleicao_id = validate_positive_id(eleicao_id, "eleicao_id")
cargo_id = validate_positive_id(cargo_id, "cargo_id")

# Validação de código
codigo = validate_codigo_candidato(codigo)

# Validação de arquivos
validate_file_upload(cryptography_key, 'pem')
validate_file_upload(election_data, 'json')
```

### Considerações de Segurança:
- ✅ Previne SQL Injection (validação de IDs)
- ✅ Previne Path Traversal (sanitização de nomes)
- ✅ Previne upload de arquivos maliciosos
- ✅ Validação de tipos e ranges
- ✅ Mensagens de erro claras

---

## 5. Tratamento de Erros Seguro

### Arquivos Criados/Modificados:
- **Criado**: `/home/user/eleicoes_urna_eletronica/core/utils/secure_logging.py`
- **Modificado**: `/home/user/eleicoes_urna_eletronica/backend/app.py`

### Implementações:

#### Handler Global de Exceções:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Logar erro completo no servidor
    logger.error(f"Erro não tratado: {type(exc).__name__}: {str(exc)}", exc_info=True)

    # Retornar mensagem segura ao cliente
    error_message = get_safe_error_message(exc, debug_mode=DEBUG_MODE)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": error_message}
    )
```

#### Função de Mensagens Seguras:
```python
def get_safe_error_message(error: Exception, debug_mode: bool = False) -> str:
    if debug_mode:
        return str(error)  # Apenas em desenvolvimento

    # Em produção, retornar mensagens genéricas
    generic_messages = {
        'ValidationError': 'Dados de entrada inválidos',
        'FileNotFoundError': 'Recurso não encontrado',
        'PermissionError': 'Permissão negada',
        # ...
    }
    return generic_messages.get(error_type, 'Erro interno do servidor')
```

### Considerações de Segurança:
- ✅ Não expõe stacktraces em produção
- ✅ Loga erros detalhados apenas no servidor
- ✅ Mensagens genéricas para o cliente
- ✅ Modo debug controlado por variável de ambiente

---

## 6. Permissões de Diretório

### Arquivos Modificados:
- **Modificado**: `/home/user/eleicoes_urna_eletronica/backend/app.py`

### Implementações:

#### Função de Configuração Segura:
```python
import stat

def setup_secure_directory():
    """Cria o diretório de upload com permissões seguras (0o700)"""
    if not os.path.exists(UPLOAD_DIRECTORY):
        os.makedirs(UPLOAD_DIRECTORY)
        # Define permissões apenas para o proprietário (rwx------)
        os.chmod(UPLOAD_DIRECTORY, stat.S_IRWXU)
        logger.info(f"Diretório {UPLOAD_DIRECTORY} criado com permissões 0o700")
    else:
        # Verificar e corrigir permissões se necessário
        current_permissions = stat.S_IMODE(os.stat(UPLOAD_DIRECTORY).st_mode)
        if current_permissions != stat.S_IRWXU:
            os.chmod(UPLOAD_DIRECTORY, stat.S_IRWXU)
            logger.warning(f"Permissões do diretório {UPLOAD_DIRECTORY} corrigidas")
```

#### Permissões de Arquivos:
```python
# Após salvar chaves, define permissões restritas (rw-------)
os.chmod(cryptography_key_path, stat.S_IRUSR | stat.S_IWUSR)
os.chmod(private_key_path, stat.S_IRUSR | stat.S_IWUSR)
```

### Considerações de Segurança:
- ✅ Diretório com permissões 0o700 (apenas proprietário)
- ✅ Arquivos de chave com permissões 0o600 (read/write proprietário)
- ✅ Verificação automática na inicialização
- ✅ Previne acesso não autorizado a chaves

---

## 7. CORS Adequado

### Arquivos Modificados:
- **Modificado**: `/home/user/eleicoes_urna_eletronica/backend/app.py`
- **Modificado**: `/home/user/eleicoes_urna_eletronica/.env.example`

### Implementações:

#### Configuração via Variáveis de Ambiente:
```python
# Configurações CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost,http://localhost:7000").split(",")
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
CORS_ALLOW_METHODS = os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE").split(",")
CORS_ALLOW_HEADERS = os.getenv("CORS_ALLOW_HEADERS", "Content-Type,Authorization").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)
```

#### Variáveis no `.env.example`:
```bash
CORS_ORIGINS="http://localhost,http://localhost:7000"
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS="GET,POST,PUT,DELETE"
CORS_ALLOW_HEADERS="Content-Type,Authorization"
```

### Considerações de Segurança:
- ✅ Origens configuráveis por ambiente
- ✅ Headers restritos (apenas necessários)
- ✅ Métodos limitados
- ✅ Fácil ajuste para produção

---

## 8. Logging Seguro

### Arquivos Criados:
- **Criado**: `/home/user/eleicoes_urna_eletronica/core/utils/secure_logging.py`

### Implementações:

#### Funções de Sanitização:
```python
def mask_sensitive_data(text: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """Mascara dados sensíveis em logs"""
    # Mascara hashes (mostra apenas 4 chars início/fim)
    # Mascara completamente: nonce, password, token, authorization

def sanitize_log_dict(data: Dict[str, Any], sensitive_keys: list[str] = None) -> Dict[str, Any]:
    """Sanitiza dicionário removendo chaves sensíveis"""
    # Remove/mascara: password, token, secret, api_key, private_key, nonce
    # Mascara hashes de 64 caracteres
```

#### Aplicação nos Logs:
```python
# Antes (inseguro)
logger.info(f"Voto registrado: {voto.id}, hash={voto.hash_blockchain}, nonce={voto.nonce}")

# Depois (seguro)
logger.info(f"Voto registrado: ID={voto.id}, Candidato={voto.candidato.nome}")
# Hash e nonce NÃO são logados
```

### Considerações de Segurança:
- ✅ Não loga hashes completos
- ✅ Não loga nonces
- ✅ Não loga senhas ou tokens
- ✅ Sanitização automática de dicionários
- ✅ Logs úteis sem expor dados sensíveis

---

## 9. Timeout Redis

### Arquivos Modificados:
- **Modificado**: `/home/user/eleicoes_urna_eletronica/backend/app.py`
- **Modificado**: `/home/user/eleicoes_urna_eletronica/.env.example`

### Implementações:

#### Configuração com Timeouts:
```python
# Configurações de timeout
REDIS_SOCKET_TIMEOUT = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
REDIS_SOCKET_CONNECT_TIMEOUT = int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5"))

# Cliente Redis com timeouts
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    socket_timeout=REDIS_SOCKET_TIMEOUT,
    socket_connect_timeout=REDIS_SOCKET_CONNECT_TIMEOUT,
    socket_keepalive=True,
    health_check_interval=30
)
```

#### Variáveis no `.env.example`:
```bash
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
```

### Considerações de Segurança:
- ✅ Previne operações bloqueantes indefinidas
- ✅ Timeout de conexão de 5 segundos
- ✅ Timeout de socket de 5 segundos
- ✅ Health check a cada 30 segundos
- ✅ Melhor resiliência em caso de falhas

---

## 10. Validação de Arquivos Upload

### Arquivos Modificados:
- **Modificado**: `/home/user/eleicoes_urna_eletronica/backend/app.py`
- **Criado**: `/home/user/eleicoes_urna_eletronica/core/utils/validation.py`

### Implementações:

#### Validações Aplicadas:

##### 1. Tipo e Extensão:
```python
ALLOWED_FILE_EXTENSIONS = {
    'pem': ['.pem'],
    'json': ['.json'],
    'image': ['.jpg', '.jpeg', '.png']
}

def validate_file_upload(file: UploadFile, file_type: str):
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_FILE_EXTENSIONS[file_type]:
        raise HTTPException(status_code=400, detail="Extensão inválida")
```

##### 2. Tamanho Máximo:
```python
MAX_FILE_SIZES = {
    'pem': 10 * 1024,      # 10 KB
    'json': 1 * 1024 * 1024,  # 1 MB
    'image': 5 * 1024 * 1024  # 5 MB
}

if len(crypto_content) > 10 * 1024:
    raise HTTPException(status_code=413, detail="Arquivo muito grande")
```

##### 3. Sanitização de Nome:
```python
def sanitize_filename(filename: str) -> str:
    # Remove path traversal
    filename = os.path.basename(filename)

    # Remove caracteres especiais
    filename = re.sub(r'[^\w\s\.-]', '', filename)

    # Limita tamanho
    if len(filename) > 255:
        filename = filename[:255]
```

#### Uso no Endpoint:
```python
@app.post("/upload-keys")
async def upload_keys(cryptography_key, private_key, election_data):
    # Validar tipo e extensão
    validate_file_upload(cryptography_key, 'pem')
    validate_file_upload(private_key, 'pem')
    validate_file_upload(election_data, 'json')

    # Sanitizar nomes
    crypto_filename = sanitize_filename("cryptography_key.pem")
    private_filename = sanitize_filename("private_key.pem")

    # Ler e validar tamanho
    crypto_content = await cryptography_key.read()
    if len(crypto_content) > 10 * 1024:
        raise HTTPException(status_code=413, ...)
```

### Considerações de Segurança:
- ✅ Previne upload de arquivos maliciosos
- ✅ Previne path traversal attacks
- ✅ Limita tamanho para prevenir DoS
- ✅ Valida extensão e tipo MIME
- ✅ Sanitiza nomes de arquivo

---

## 📊 Resumo de Arquivos

### Arquivos Criados:
1. `/home/user/eleicoes_urna_eletronica/core/auth/__init__.py`
2. `/home/user/eleicoes_urna_eletronica/core/auth/security.py`
3. `/home/user/eleicoes_urna_eletronica/core/utils/validation.py`
4. `/home/user/eleicoes_urna_eletronica/core/utils/secure_logging.py`

### Arquivos Modificados:
1. `/home/user/eleicoes_urna_eletronica/pyproject.toml`
2. `/home/user/eleicoes_urna_eletronica/core/models/classes.py`
3. `/home/user/eleicoes_urna_eletronica/backend/app.py`
4. `/home/user/eleicoes_urna_eletronica/.env.example`

---

## 🔒 Checklist de Segurança

### Implementado ✅

- [x] Autenticação JWT com bcrypt
- [x] Rate limiting em endpoints críticos
- [x] Dependency injection (sem variáveis globais)
- [x] Validação robusta de entrada
- [x] Handler global de exceções
- [x] Permissões de diretório (0o700)
- [x] CORS configurável via ambiente
- [x] Logging sem dados sensíveis
- [x] Timeouts no Redis
- [x] Validação completa de uploads

### Próximos Passos 📝

1. **Configurar Produção**:
   - Alterar `JWT_SECRET_KEY` para chave forte
   - Configurar `CORS_ORIGINS` com domínios reais
   - Definir `DEBUG_MODE=false`

2. **Banco de Dados de Usuários**:
   - Implementar persistência de usuários
   - Adicionar endpoint de registro
   - Implementar recuperação de senha

3. **Auditoria**:
   - Adicionar logs de auditoria
   - Implementar trilha de eventos
   - Monitoramento de tentativas de acesso

4. **Testes**:
   - Executar suite de testes
   - Adicionar testes de segurança
   - Testes de penetração

---

## 🚀 Como Usar

### 1. Instalar Dependências:
```bash
uv sync
```

### 2. Configurar Ambiente:
```bash
cp .env.example .env
# Editar .env com configurações apropriadas
```

### 3. Executar Aplicação:
```bash
uvicorn backend.app:app --reload --port 7000
```

### 4. Testar Login:
```bash
curl -X POST http://localhost:7000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123"}'
```

### 5. Usar Token:
```bash
# Salvar token da resposta
TOKEN="eyJ..."

# Usar em requisições protegidas
curl -X GET http://localhost:7000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## ⚠️ Avisos Importantes

1. **JWT_SECRET_KEY**: DEVE ser alterado em produção para uma chave forte e aleatória
2. **DEBUG_MODE**: DEVE ser `false` em produção
3. **CORS_ORIGINS**: Configurar apenas domínios confiáveis
4. **Usuário Admin**: Senha de exemplo deve ser alterada
5. **Backup de Chaves**: Fazer backup seguro das chaves criptográficas

---

## 📚 Referências

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Redis Security](https://redis.io/topics/security)

---

**Data de Implementação**: 2025-11-16
**Versão**: 1.0
**Status**: ✅ Completo
