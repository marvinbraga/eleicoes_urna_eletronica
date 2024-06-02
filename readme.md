# Sistema de Votação Eletrônica

_Por Marcus Vinicius Braga_

Este é um projeto de sistema de votação eletrônica desenvolvido em Python. O objetivo é fornecer uma solução segura e
confiável para o processo de votação, garantindo a integridade dos votos e a transparência dos resultados.

## Funcionalidades

- Registro de candidatos, partidos, cargos e eleições
- Votação eletrônica segura
- Geração de registros impressos dos votos
- Validação dos votos
- Geração do Boletim de Urna
- Validação do Boletim de Urna
- Geração do Registro de Urna
- Totalização dos votos
- Verificação da integridade da totalização
- Detecção de anomalias após a totalização
- Detecção de conluio após a totalização

## Tecnologias utilizadas

- Python 3.x
- Pydantic
- Cryptography
- Poetry (gerenciador de dependências e ambiente virtual)

## Estrutura do projeto

```
.
├── blockchain/
│   └── classes.py
├── models/
│   ├── __init__.py
│   └── classes.py
├── processors/
│   ├── __init__.py
│   └── classes.py
├── resources/
│   ├── private_key.pem
│   └── cryptography_key.pem
├── security/
│   ├── arquivos de logs...
├── utils/
│   ├── __init__.py
│   └── security.py
│   └── ...
├── main.py
├── pyproject.toml
└── readme.md
```

Aqui está uma explicação de cada diretório e arquivo:

- `blockchain/`: Diretório para implementação relacionada à tecnologia blockchain.
- `models/`: Diretório para classes de modelo, como Candidato, Partido, Cargo e Eleicao.
  - `classes.py`: Definição das classes de modelo, como Candidato, Partido, Cargo e Eleicao.
- `processors/`: Diretório para classes de processamento, como SistemaVotacao.
  - `classes.py`: Implementação da classe SistemaVotacao, responsável pelo processamento da 
    votação e operações relacionadas.
- `resources/`: Diretório para armazenar recursos, como chaves de criptografia.
  - `private_key.pem`: Arquivo contendo a chave privada.
  - `cryptography_key.pem`: Arquivo contendo a chave de criptografia.
- `security/`: Diretório para classes relacionadas à segurança.
- `utils/`: Diretório para utilitários e funções auxiliares.
  - `security.py`: Implementação das classes KeyManager e CryptographyKeyManager para gerenciamento das 
    chaves de criptografia. 
- `main.py`: Arquivo principal que contém o exemplo de uso do sistema de votação.
- `pyproject.toml`: Arquivo de configuração do Poetry para gerenciar as dependências do projeto.
- `readme.md`: Arquivo de documentação do projeto.

## Configuração e execução

1. Certifique-se de ter o Python ^3.10 e o Poetry instalados em seu sistema.
2. Clone este repositório em sua máquina local.
3. Navegue até o diretório raiz do projeto.
4. Execute o seguinte comando para instalar as dependências do projeto:
   ```bash
   poetry install
   ```
5. Ative o ambiente virtual criado pelo Poetry:
   ```bash
   poetry shell
   ```
6. Execute o arquivo `main.py` para iniciar o exemplo de uso do sistema de votação:
   ```bash
   python main.py
   ```

## Licença

Este projeto está licenciado sob a GNU General Public License v3.0. Consulte o arquivo [LICENSE](LICENSE) para obter
mais informações.

## Contribuição

Contribuições são bem-vindas! Se você encontrar algum problema, tiver sugestões ou quiser adicionar novos recursos,
sinta-se à vontade para abrir uma issue ou enviar um pull request.

## Aviso Legal

Este projeto é fornecido "como está", sem garantias de qualquer tipo, expressas ou implícitas. Os autores não se
responsabilizam por quaisquer danos diretos, indiretos, incidentais, especiais, exemplares ou consequentes relacionados
ao uso deste software.

## Detalhamento das Informações

### Votação

1. O eleitor seleciona o candidato na urna eletrônica:
    - O eleitor interage com a interface da urna eletrônica para escolher o candidato de sua preferência.

2. O sistema gera o registro de voto e deve salvá-lo de acordo com a digitação, utilizando tecnologia Block Chain:
    - Após a seleção do candidato, o sistema cria um registro de voto contendo as informações do voto.
    - O registro de voto é salvo em uma estrutura de dados baseada em Block Chain, garantindo a integridade e
      imutabilidade dos votos.

3. O eleitor pode conferir seu voto através da tela da urna:
    - Após a digitação do voto, o eleitor tem a oportunidade de verificar as informações do voto na tela da urna
      eletrônica.

4. O registro impresso deve ser gerado a partir do registro salvo e não do digitado para evitar divergências entre a
   informação que será gravada e a que estará impressa. As informações que deverão ser impressas são:
    - Hash de localização do voto na listagem de votos da urna.
    - Todos os dados dos candidatos que são apresentados na tela da urna.
    - Hash de registro do Block Chain.
    - QR Code com todas estas informações.

5. O eleitor pode conferir seu voto através do registro impresso:
    - Após a impressão do registro de voto, o eleitor pode verificar manualmente se as informações impressas
      correspondem ao seu voto.

6. O eleitor confirma seu voto e o sistema deve mantê-lo gravado sem quaisquer informações relacionadas ao eleitor (
   garante o segredo do voto):
    - Após a confirmação do eleitor, o sistema grava o voto de forma anônima, sem associá-lo a informações que possam
      identificar o eleitor, garantindo o sigilo do voto.

### Validação dos Votos

1. Os fiscais partidários e todos os outros interessados podem executar o escrutínio público utilizando o registro
   impresso do voto:
    - Os fiscais e outros interessados têm acesso aos registros impressos dos votos para realizar a contagem manual e
      verificar a integridade do processo de votação.

2. O sistema captura o registro impresso do voto através da leitura do QR Code para apresentação dos dados do voto e
   comparação com o registro impresso. Feita a conferência, o sistema irá salvá-lo para a contabilização do Boletim de
   Urna (BU):
    - O sistema utiliza a leitura do QR Code presente no registro impresso para capturar os dados do voto.
    - Os dados capturados são comparados com as informações impressas para verificar a consistência.
    - Após a conferência, o sistema salva o registro do voto para posterior contabilização no Boletim de Urna.

3. É feita a conferência de todos os registros dos votos com os registros impressos capturados:
    - Todos os registros de votos são comparados com os registros impressos capturados para garantir a integridade dos
      votos.

4. Todos os presentes serão informados em caso de existência de problemas na conferência dos votos:
    - Se houver discrepâncias ou problemas durante a conferência dos votos, todos os presentes serão notificados.

### Criação do Boletim de Urna (BU)

1. O sistema totaliza e imprime o BU. O BU deve ser impresso com:
    - O hash final do Block Chain dos votos da urna.
    - Todas as informações do BU.
    - O hash destas informações do BU.
    - O QR Code dos hashes e informações do BU.

2. O sistema captura o BU para conferência de dados através da leitura do QR Code:
    - O sistema utiliza a leitura do QR Code presente no BU impresso para capturar os dados do BU.

### Validação do Boletim de Urna (BU)

1. É feita a conferência do registro do BU salvo com o registro de BU capturado através do comprovante impresso:
    - O registro do BU salvo é comparado com o registro do BU capturado a partir do comprovante impresso para verificar
      a consistência.

2. Todos os presentes serão informados em caso de existência de problemas na conferência dos BUs:
    - Se houver discrepâncias ou problemas durante a conferência dos BUs, todos os presentes serão notificados.

3. Todas as autoridades exigidas pela legislação deverão assinar o BU:
    - As autoridades competentes devem assinar o BU para atestar sua validade e conformidade com a legislação.

### Criação do Registro de Urna

1. O sistema deverá capturar através de escaneamento o BU assinado por todas as autoridades exigidas pela legislação. O
   sistema deverá persistir esta informação de forma criptografada e compactada:
    - O BU assinado é escaneado e capturado pelo sistema.
    - As informações do BU escaneado são criptografadas e compactadas antes de serem armazenadas.

2. O sistema gera o registro de urna com a data e hora do servidor, registro do BU escaneado e registro eletrônico do
   BU (o qual foi validado no processo anterior):
    - O registro de urna é criado contendo a data e hora do servidor, o registro do BU escaneado e o registro eletrônico
      do BU previamente validado.

### Envio do Registro de Urna

1. O sistema compacta, criptografa e envia todas as informações do registro de urna:
    - As informações do registro de urna são compactadas e criptografadas antes de serem enviadas para garantir a
      segurança e a integridade dos dados.

### Processamento do Registro de Urna

1. O processamento da urna irá capturar o registro de urna e verificar se o hash deste registro é idêntico ao hash do
   documento escaneado:
    - O sistema de processamento captura o registro de urna e calcula o hash do registro.
    - O hash calculado é comparado com o hash do documento escaneado para verificar a integridade do registro.

2. O processamento irá gerar uma hash com as informações capturadas do registro de urna atual e compará-lo com o hash do
   registro salvo e, somente assim, poderá processá-lo:
    - O sistema gera um hash com as informações capturadas do registro de urna atual.
    - O hash gerado é comparado com o hash do registro salvo para verificar a consistência.
    - Somente após a verificação bem-sucedida, o registro de urna pode ser processado.

3. Finalizado o processamento do registro de urna, o sistema salvará o registro de urna juntamente com o hash gerado
   para sua contabilização, incluindo a data e hora automática do servidor:
    - Após o processamento, o registro de urna é salvo juntamente com o hash gerado.
    - A data e hora automática do servidor são incluídas no registro para fins de contabilização.

### Totalização

1. A totalização deve ser feita utilizando a tecnologia Block Chain:
    - A totalização dos votos é realizada utilizando a tecnologia Block Chain para garantir a integridade e a
      transparência do processo.
    - A estrutura de dados baseada em Block Chain permite a verificação e a auditoria dos votos de forma segura e
      confiável.

---

**eleicoes_urna_eletronica**
