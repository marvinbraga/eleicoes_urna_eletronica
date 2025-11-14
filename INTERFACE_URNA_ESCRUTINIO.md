# Interfaces da Urna Eletrônica e Escrutínio

Este documento descreve as novas interfaces criadas para o Sistema de Votação Eletrônica.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Interface da Urna Eletrônica](#interface-da-urna-eletrônica)
3. [Interface de Escrutínio](#interface-de-escrutínio)
4. [Como Usar](#como-usar)
5. [Tecnologias Utilizadas](#tecnologias-utilizadas)

## 🎯 Visão Geral

Foram criadas duas interfaces modernas e responsivas:

1. **Urna Eletrônica** (`/urna.html`) - Interface que emula uma urna eletrônica real
2. **Escrutínio** (`/escrutinio.html`) - Interface para contagem pública e visualização de resultados

## 🗳️ Interface da Urna Eletrônica

### Características

- **Design Realista**: Interface que emula visualmente uma urna eletrônica brasileira
- **Teclado Virtual**: Teclado numérico completo (0-9) + botões especiais
- **Botões Especiais**:
  - 🟢 **CONFIRMA**: Confirma o voto
  - 🟠 **CORRIGE**: Corrige o número digitado
  - ⚪ **BRANCO**: Vota em branco
- **Display Interativo**: Mostra informações do candidato, foto, partido e número
- **Suporte a Teclado Físico**:
  - Números 0-9: Digita o número
  - Enter: Confirma o voto
  - Backspace: Corrige
  - Espaço: Voto em branco

### Fluxo de Votação

1. **Inicialização**: Upload das chaves e arquivo JSON da eleição
2. **Seleção de Cargo**: Escolha do cargo para votação
3. **Digitação**: Digite o número do candidato
4. **Visualização**: Veja as informações do candidato
5. **Confirmação**: Confirme ou corrija o voto
6. **Próximo Cargo**: Sistema avança automaticamente para o próximo cargo
7. **Finalização**: Mensagem de conclusão

### Recursos de Segurança

- ✅ Conexão criptografada
- ✅ Validação em tempo real
- ✅ Feedback visual e de status
- ✅ Contador de votos

### Arquivos

- `backend/templates/urna.html` - Estrutura HTML
- `backend/static/urna.css` - Estilos visuais
- `backend/static/urna.js` - Lógica e interatividade

## 📊 Interface de Escrutínio

### Características

- **Painel de Controle**:
  - Botão para totalizar votos
  - Botão para atualizar resultados
  - Botão para gerar boletim de urna
  - Toggle de atualização automática (a cada 5 segundos)

- **Estatísticas em Tempo Real**:
  - Total de votos
  - Votos válidos
  - Votos em branco
  - Votos nulos

- **Resultados por Cargo**:
  - Ranking de candidatos com medalhas (🥇🥈🥉)
  - Foto, nome, partido e número do candidato
  - Número de votos e percentual
  - Barra de progresso visual
  - Destaque para o vencedor

- **Gráficos Interativos**:
  - Gráfico de pizza: Distribuição geral (válidos, brancos, nulos)
  - Gráfico de barras: Top 10 candidatos mais votados
  - Cores dinâmicas e animações

- **Boletim de Urna (BU)**:
  - Informações completas da urna (seção, zona, município, estado)
  - Hash final da blockchain
  - Hash do boletim de urna
  - Certificação de assinatura digital

- **Auditoria e Segurança**:
  - Status da integridade blockchain
  - Verificação de assinatura digital
  - Hashes completos para auditoria

### Funcionalidades

#### Atualização Manual
Clique em "Atualizar Resultados" para obter os dados mais recentes.

#### Atualização Automática
Ative o toggle "Atualização Automática" para receber atualizações a cada 5 segundos.

#### Visualização de Gráficos
Gráficos são gerados automaticamente após a totalização usando Chart.js.

#### Geração de Boletim
O botão "Gerar Boletim de Urna" cria um documento oficial com:
- Dados da urna
- Total de votos
- Hashes de segurança
- Assinatura digital

### Arquivos

- `backend/templates/escrutinio.html` - Estrutura HTML
- `backend/static/escrutinio.css` - Estilos visuais
- `backend/static/escrutinio.js` - Lógica, gráficos e atualização

## 🚀 Como Usar

### 1. Iniciar o Sistema

```bash
# Iniciar o Redis
redis-server

# Iniciar o backend FastAPI
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 7000
```

### 2. Acessar as Interfaces

- **Página Principal (Admin)**: http://localhost:7000/
- **Urna Eletrônica**: http://localhost:7000/urna.html
- **Escrutínio**: http://localhost:7000/escrutinio.html

### 3. Fluxo Completo de Uso

#### Passo 1: Inicializar a Urna
1. Acesse `/urna.html`
2. Faça upload dos arquivos:
   - Chave de criptografia (`.pem`)
   - Chave privada (`.pem`)
   - Dados da eleição (`.json`)
3. Clique em "Inicializar Urna"

#### Passo 2: Votar
1. Selecione o cargo
2. Digite o número do candidato
3. Verifique as informações
4. Pressione CONFIRMA
5. Repita para os próximos cargos
6. Conclusão da votação

#### Passo 3: Acompanhar Escrutínio
1. Acesse `/escrutinio.html`
2. Clique em "Totalizar Votos"
3. Visualize as estatísticas
4. Analise os gráficos
5. (Opcional) Ative atualização automática
6. Gere o Boletim de Urna

### 4. Navegação entre Páginas

Cada interface possui botões de navegação:
- Da Urna → Escrutínio ou Administração
- Do Escrutínio → Urna ou Administração
- Da Administração → Urna ou Escrutínio

## 🛠️ Tecnologias Utilizadas

### Frontend
- **HTML5**: Estrutura semântica
- **Bootstrap 4.5.2**: Framework CSS responsivo
- **Font Awesome 5.15.4**: Ícones
- **jQuery 3.5.1**: Manipulação DOM e AJAX
- **Chart.js 3.9.1**: Gráficos interativos

### Backend
- **FastAPI**: Framework web Python
- **Jinja2**: Template engine
- **Redis**: Cache e armazenamento
- **Cryptography**: Segurança e criptografia

### Design
- **Gradientes CSS**: Visual moderno
- **Animações CSS**: Transições suaves
- **Responsividade**: Mobile-first design
- **Acessibilidade**: ARIA labels e contraste

## 🎨 Personalização

### Cores da Urna
Edite `urna.css` para alterar o esquema de cores:
- Display: Azul e amarelo (cores oficiais)
- Botão CONFIRMA: Verde
- Botão CORRIGE: Laranja
- Botão BRANCO: Branco

### Cores do Escrutínio
Edite `escrutinio.css`:
- Cards de estatísticas: Gradientes personalizados
- Gráficos: Cores dinâmicas em `escrutinio.js`

### Tempo de Atualização Automática
Edite `escrutinio.js` linha 436:
```javascript
// Alterar 5000ms (5 segundos) para o valor desejado
appState.refreshInterval = setInterval(() => {
    totalizarVotos();
}, 5000); // Mudar aqui
```

## 📱 Responsividade

Ambas as interfaces são totalmente responsivas:

- **Desktop**: Layout completo com todos os recursos
- **Tablet**: Layout adaptado com grid responsivo
- **Mobile**: Layout vertical otimizado para touch

## 🔒 Segurança

### Urna Eletrônica
- Comunicação HTTPS (em produção)
- Validação de entrada
- Proteção contra duplicação
- Criptografia de votos

### Escrutínio
- Verificação de integridade blockchain
- Assinatura digital RSA-2048
- Hashes SHA-256
- Auditoria completa

## 📈 Gráficos e Visualizações

### Gráfico de Distribuição (Pizza)
- Mostra proporção entre votos válidos, brancos e nulos
- Cores diferenciadas
- Tooltips com percentuais

### Gráfico de Candidatos (Barras)
- Top 10 candidatos mais votados
- Cores únicas para cada candidato
- Escala automática

### Ranking Visual
- Medalhas para os 3 primeiros colocados
- Barras de progresso animadas
- Efeito shimmer no vencedor

## 🐛 Solução de Problemas

### Urna não inicializa
- Verifique se o Redis está rodando
- Confirme que os arquivos `.pem` e `.json` estão corretos
- Verifique os logs do backend

### Gráficos não aparecem
- Certifique-se de que Chart.js foi carregado
- Verifique o console do navegador
- Clique em "Totalizar Votos" primeiro

### Atualização automática não funciona
- Desative e ative o toggle novamente
- Verifique se há votos registrados
- Confirme a conexão com o backend

## 📝 Notas Importantes

1. **Primeira Utilização**: Sempre inicialize a urna antes de votar
2. **Dados de Teste**: Use o arquivo `resources/eleicao.json`
3. **Chaves de Segurança**: Gere suas próprias chaves para produção
4. **Performance**: A atualização automática aumenta o tráfego de rede
5. **Navegadores**: Testado em Chrome, Firefox, Safari e Edge

## 🎓 Recursos Educacionais

Este sistema demonstra:
- Criptografia aplicada
- Blockchain para auditoria
- Design de interface de usuário
- Arquitetura cliente-servidor
- Visualização de dados
- Responsividade web

---

**Desenvolvido para fins educacionais e demonstração do processo eleitoral eletrônico.**
