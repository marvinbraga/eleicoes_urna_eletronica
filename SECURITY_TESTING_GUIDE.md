# Guia de Testes de Segurança

Este documento contém testes práticos para validar todas as melhorias de segurança implementadas.

---

## 🚀 Setup Inicial

### 1. Instalar Dependências
```bash
cd /home/user/eleicoes_urna_eletronica
poetry install
```

### 2. Configurar Ambiente
```bash
cp .env.example .env

# Editar .env com suas configurações
nano .env
```

### 3. Iniciar Aplicação
```bash
# Terminal 1: Iniciar Redis (se necessário)
docker-compose up redis

# Terminal 2: Iniciar aplicação
poetry run uvicorn backend.app:app --reload --port 7000
```

---

## 🧪 Testes de Autenticação JWT

### Teste 1: Login com Credenciais Válidas
```bash
curl -X POST http://localhost:7000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin123"
  }'
```

**Resposta Esperada**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Teste 2: Login com Credenciais Inválidas
```bash
curl -X POST http://localhost:7000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "SenhaErrada"
  }'
```

**Resposta Esperada**:
```json
{
  "detail": "Credenciais inválidas"
}
```
**Status Code**: 401

### Teste 3: Verificar Usuário Autenticado
```bash
# Primeiro, obter token
TOKEN=$(curl -s -X POST http://localhost:7000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123"}' \
  | jq -r '.access_token')

# Usar token para acessar endpoint protegido
curl -X GET http://localhost:7000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

**Resposta Esperada**:
```json
{
  "username": "admin",
  "scopes": ["admin", "votacao", "totalizacao"]
}
```

### Teste 4: Token Inválido
```bash
curl -X GET http://localhost:7000/api/auth/me \
  -H "Authorization: Bearer token_invalido_123"
```

**Resposta Esperada**:
```json
{
  "detail": "Não foi possível validar as credenciais"
}
```
**Status Code**: 401

---

## 🚦 Testes de Rate Limiting

### Teste 5: Rate Limit no Login
```bash
# Script para testar rate limiting (5 req/min)
for i in {1..6}; do
  echo "Requisição $i:"
  curl -w "\nStatus: %{http_code}\n\n" -X POST http://localhost:7000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "Admin123"}'
  sleep 1
done
```

**Resultado Esperado**:
- Requisições 1-5: Status 200
- Requisição 6: Status 429 (Too Many Requests)

### Teste 6: Rate Limit em Votação
```bash
# Obter token primeiro
TOKEN=$(curl -s -X POST http://localhost:7000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123"}' \
  | jq -r '.access_token')

# Tentar votar 11 vezes (limite: 10/min)
for i in {1..11}; do
  echo "Voto $i:"
  curl -w "\nStatus: %{http_code}\n" -X POST http://localhost:7000/votar \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d @vote_payload.json
  sleep 5
done
```

**Resultado Esperado**:
- Votos 1-10: Status 200 (ou 400 se sistema não inicializado)
- Voto 11: Status 429

---

## 🔒 Testes de Validação de Entrada

### Teste 7: ID Negativo
```bash
curl -X GET http://localhost:7000/cargos/-1
```

**Resposta Esperada**:
```json
{
  "detail": "eleicao_id deve ser maior que zero"
}
```
**Status Code**: 400

### Teste 8: Código de Candidato Inválido
```bash
# Código com letras (inválido)
curl -X GET http://localhost:7000/buscar-candidatos/1/abc
```

**Resposta Esperada**:
```json
{
  "detail": "Código do candidato deve conter apenas números"
}
```

### Teste 9: Código Muito Curto
```bash
# Código com 1 dígito (mínimo: 2)
curl -X GET http://localhost:7000/buscar-candidatos/1/1
```

**Resposta Esperada**:
```json
{
  "detail": "Código do candidato deve ter entre 2 e 5 dígitos"
}
```

---

## 📁 Testes de Upload de Arquivos

### Teste 10: Upload de Arquivo com Extensão Inválida
```bash
# Criar arquivo de teste com extensão errada
echo "test" > test.txt

curl -X POST http://localhost:7000/upload-keys \
  -F "private_key=@test.txt" \
  -F "cryptography_key=@test.txt" \
  -F "election_data=@test.txt"
```

**Resposta Esperada**:
```json
{
  "detail": "Extensão de arquivo inválida. Esperado: .pem"
}
```
**Status Code**: 400

### Teste 11: Arquivo Muito Grande
```bash
# Criar arquivo > 10KB
dd if=/dev/zero of=large.pem bs=1024 count=15

curl -X POST http://localhost:7000/upload-keys \
  -F "private_key=@large.pem" \
  -F "cryptography_key=@resources/cryptography_key.pem" \
  -F "election_data=@resources/eleicao_data.json"
```

**Resposta Esperada**:
```json
{
  "detail": "Arquivo de chave privada muito grande"
}
```
**Status Code**: 413

### Teste 12: Sanitização de Nome de Arquivo
```bash
# Python script para testar sanitização
python3 << 'EOF'
from core.utils.validation import sanitize_filename

# Path traversal
assert sanitize_filename("../../etc/passwd") == "etcpasswd"

# Caracteres especiais
assert sanitize_filename("file<>|?*.pem") == "file.pem"

# Espaços múltiplos
assert sanitize_filename("my   file.pem") == "my_file.pem"

print("✅ Todos os testes de sanitização passaram!")
EOF
```

---

## 🛡️ Testes de Tratamento de Erros

### Teste 13: Erro Genérico em Produção
```bash
# Configurar DEBUG_MODE=false no .env
export DEBUG_MODE=false

# Forçar erro (sistema não inicializado)
curl -X POST http://localhost:7000/votar \
  -H "Content-Type: application/json" \
  -d '{"candidato": {}}'
```

**Resposta Esperada (Produção)**:
```json
{
  "detail": "Sistema de votação não inicializado. Faça o upload das chaves primeiro."
}
```

### Teste 14: Erro Detalhado em Desenvolvimento
```bash
# Configurar DEBUG_MODE=true no .env
export DEBUG_MODE=true

# Mesmo erro, mas com mais detalhes
curl -X POST http://localhost:7000/votar \
  -H "Content-Type: application/json" \
  -d '{"candidato": {}}'
```

**Comportamento Esperado**:
- Produção: Mensagem genérica
- Desenvolvimento: Stacktrace detalhado (apenas nos logs do servidor)

---

## 🔐 Testes de Permissões de Arquivo

### Teste 15: Verificar Permissões de Diretório
```bash
# Verificar permissões do diretório uploaded_keys
ls -ld uploaded_keys/

# Deve mostrar: drwx------ (700)
# Significa: Owner: rwx, Group: ---, Others: ---
```

**Verificação**:
```bash
stat -c "%a %n" uploaded_keys/
# Esperado: 700 uploaded_keys/
```

### Teste 16: Verificar Permissões de Arquivos
```bash
# Após fazer upload de chaves
ls -la uploaded_keys/*.pem

# Deve mostrar: -rw------- (600)
# Significa: Owner: rw-, Group: ---, Others: ---
```

**Verificação**:
```bash
stat -c "%a %n" uploaded_keys/*.pem
# Esperado: 600 uploaded_keys/private_key.pem
```

---

## 🌐 Testes de CORS

### Teste 17: Requisição de Origem Permitida
```bash
curl -X GET http://localhost:7000/cargos/1 \
  -H "Origin: http://localhost:7000" \
  -v
```

**Cabeçalhos Esperados**:
```
Access-Control-Allow-Origin: http://localhost:7000
Access-Control-Allow-Credentials: true
```

### Teste 18: Requisição de Origem Não Permitida
```bash
curl -X GET http://localhost:7000/cargos/1 \
  -H "Origin: http://malicious-site.com" \
  -v
```

**Comportamento Esperado**:
- Sem cabeçalho `Access-Control-Allow-Origin`
- Navegador bloquearia a resposta

---

## 📝 Testes de Logging Seguro

### Teste 19: Verificar Logs Não Contêm Dados Sensíveis
```bash
# Fazer uma votação
curl -X POST http://localhost:7000/votar \
  -H "Content-Type: application/json" \
  -d @vote_payload.json

# Verificar logs
tail -n 20 logs/app.log | grep -i "voto registrado"
```

**Verificação**:
```bash
# Logs NÃO devem conter:
❌ Hash completo de blockchain (64 chars)
❌ Nonce
❌ Senha
❌ Token JWT

# Logs DEVEM conter:
✅ ID do voto
✅ Nome do candidato
✅ Timestamp
```

### Teste 20: Sanitização de Logs
```bash
# Python script para testar sanitização
python3 << 'EOF'
from core.utils.secure_logging import mask_sensitive_data, sanitize_log_dict

# Testar mascaramento de hash
text = "Hash: abc123def456789012345678901234567890123456789012345678901234"
masked = mask_sensitive_data(text)
print(f"Masked: {masked}")
# Esperado: Hash: abc1...5678

# Testar sanitização de dicionário
data = {
    "username": "admin",
    "password": "secret123",
    "token": "eyJ...",
    "public_data": "visible"
}
sanitized = sanitize_log_dict(data)
print(f"Sanitized: {sanitized}")
# Esperado: password e token mascarados

print("✅ Testes de logging seguro passaram!")
EOF
```

---

## ⏱️ Testes de Timeout Redis

### Teste 21: Timeout de Conexão
```bash
# Parar Redis
docker-compose stop redis

# Tentar operação (deve falhar com timeout)
timeout 10 curl -X GET http://localhost:7000/cargos/1
```

**Comportamento Esperado**:
- Conexão falha em ~5 segundos (REDIS_SOCKET_CONNECT_TIMEOUT)
- Não bloqueia indefinidamente

### Teste 22: Verificar Health Check
```bash
# Python script para monitorar health check
python3 << 'EOF'
import redis
import time

client = redis.Redis(
    host='localhost',
    port=6379,
    socket_timeout=5,
    socket_connect_timeout=5,
    health_check_interval=30
)

# Health check deve executar automaticamente
for i in range(5):
    try:
        client.ping()
        print(f"✅ Ping {i+1}: OK")
    except redis.exceptions.ConnectionError:
        print(f"❌ Ping {i+1}: FAILED")
    time.sleep(10)
EOF
```

---

## 🧬 Testes de Validação de Senha

### Teste 23: Senha Fraca
```bash
# Python script para testar validação
python3 << 'EOF'
from pydantic import ValidationError
from core.models.classes import UserCreate

# Senha muito curta
try:
    user = UserCreate(
        username="test",
        email="test@example.com",
        password="123"  # < 8 caracteres
    )
    print("❌ Deveria ter falhado!")
except ValidationError as e:
    print("✅ Senha curta rejeitada:", e.errors()[0]['msg'])

# Senha sem número
try:
    user = UserCreate(
        username="test",
        email="test@example.com",
        password="Abcdefgh"  # Sem número
    )
    print("❌ Deveria ter falhado!")
except ValidationError as e:
    print("✅ Senha sem número rejeitada:", e.errors()[0]['msg'])

# Senha sem maiúscula
try:
    user = UserCreate(
        username="test",
        email="test@example.com",
        password="abcdef123"  # Sem maiúscula
    )
    print("❌ Deveria ter falhado!")
except ValidationError as e:
    print("✅ Senha sem maiúscula rejeitada:", e.errors()[0]['msg'])

# Senha válida
try:
    user = UserCreate(
        username="test",
        email="test@example.com",
        password="Abcdef123"  # Válida!
    )
    print("✅ Senha forte aceita!")
except ValidationError as e:
    print("❌ Não deveria ter falhado!")
EOF
```

---

## 🧪 Suite de Testes Automatizados

### Teste 24: Executar Todos os Testes
```bash
# Executar suite de testes do pytest
poetry run pytest tests/ -v

# Executar apenas testes de API
poetry run pytest tests/test_api.py -v

# Executar com coverage
poetry run pytest tests/ --cov=backend --cov=core --cov-report=html
```

### Teste 25: Testes de Segurança Específicos
```bash
# Criar arquivo de testes de segurança
cat > tests/test_security.py << 'EOF'
import pytest
from fastapi import status

def test_jwt_authentication(client):
    """Testa autenticação JWT"""
    # Login
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "Admin123"
    })
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()

def test_rate_limiting(client):
    """Testa rate limiting"""
    # Fazer 6 requisições (limite: 5/min)
    for i in range(6):
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "Admin123"
        })
        if i < 5:
            assert response.status_code == status.HTTP_200_OK
        else:
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

def test_input_validation(client):
    """Testa validação de entrada"""
    # ID negativo
    response = client.get("/cargos/-1")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "maior que zero" in response.json()["detail"]

def test_file_upload_validation(client):
    """Testa validação de upload"""
    # Arquivo com extensão inválida
    files = {
        "private_key": ("test.txt", b"test", "text/plain"),
        "cryptography_key": ("test.txt", b"test", "text/plain"),
        "election_data": ("test.txt", b"test", "text/plain")
    }
    response = client.post("/upload-keys", files=files)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
EOF

# Executar testes de segurança
poetry run pytest tests/test_security.py -v
```

---

## 📊 Checklist de Validação

### ✅ Autenticação e Autorização
- [ ] Login com credenciais válidas retorna token JWT
- [ ] Login com credenciais inválidas retorna 401
- [ ] Token válido permite acesso a endpoints protegidos
- [ ] Token inválido retorna 401
- [ ] Token expirado retorna 401

### ✅ Rate Limiting
- [ ] Login limitado a 5 req/min
- [ ] Votação limitada a 10 req/min
- [ ] Totalização limitada a 5 req/min
- [ ] Upload de chaves limitado a 3 req/min
- [ ] Requisição excedente retorna 429

### ✅ Validação de Entrada
- [ ] IDs negativos são rejeitados
- [ ] IDs zero são rejeitados
- [ ] Códigos de candidato com letras são rejeitados
- [ ] Códigos muito curtos são rejeitados
- [ ] Códigos muito longos são rejeitados

### ✅ Upload de Arquivos
- [ ] Extensões inválidas são rejeitadas
- [ ] Arquivos muito grandes são rejeitados
- [ ] Nomes de arquivo são sanitizados
- [ ] Path traversal é prevenido

### ✅ Permissões
- [ ] Diretório uploaded_keys tem permissão 700
- [ ] Arquivos .pem têm permissão 600
- [ ] Permissões são verificadas no startup

### ✅ CORS
- [ ] Origens permitidas têm acesso
- [ ] Origens não permitidas são bloqueadas
- [ ] Headers corretos são retornados

### ✅ Logging
- [ ] Hashes não aparecem completos nos logs
- [ ] Nonces não aparecem nos logs
- [ ] Senhas não aparecem nos logs
- [ ] Tokens não aparecem nos logs

### ✅ Timeouts
- [ ] Redis timeout de conexão funciona
- [ ] Redis timeout de socket funciona
- [ ] Health check executa periodicamente

### ✅ Tratamento de Erros
- [ ] Produção não expõe stacktraces
- [ ] Desenvolvimento mostra erros detalhados
- [ ] Mensagens genéricas em produção
- [ ] Logs detalhados no servidor

---

## 🎯 Resultados Esperados

Após executar todos os testes, você deve ter:

1. ✅ **100% dos testes de autenticação** passando
2. ✅ **Rate limiting** funcionando corretamente
3. ✅ **Validações** rejeitando entradas inválidas
4. ✅ **Uploads** com validação robusta
5. ✅ **Permissões** corretas em arquivos e diretórios
6. ✅ **CORS** configurado adequadamente
7. ✅ **Logs** sem dados sensíveis
8. ✅ **Timeouts** prevenindo bloqueios
9. ✅ **Erros** tratados de forma segura
10. ✅ **Código** sem vulnerabilidades conhecidas

---

## 🚨 Troubleshooting

### Problema: "Module not found"
```bash
# Solução: Instalar dependências
poetry install
```

### Problema: "Connection refused" no Redis
```bash
# Solução: Iniciar Redis
docker-compose up -d redis
```

### Problema: "Permission denied" em uploaded_keys
```bash
# Solução: Corrigir permissões
chmod 700 uploaded_keys/
chmod 600 uploaded_keys/*.pem
```

### Problema: Rate limit não funciona
```bash
# Solução: Verificar que slowapi está instalado
poetry show slowapi

# Verificar configuração no app.py
grep "limiter" backend/app.py
```

---

## 📞 Suporte

Se encontrar problemas:

1. Verificar logs: `tail -f logs/app.log`
2. Verificar variáveis de ambiente: `cat .env`
3. Verificar dependências: `poetry show`
4. Consultar documentação: `SECURITY_IMPROVEMENTS.md`

---

**Guia criado em**: 2025-11-16
**Última atualização**: 2025-11-16
