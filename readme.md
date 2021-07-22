# Processo de Urna Eletrônica
_Por Marcus Vinicius Braga_

## Votação

- O eleitor seleciona o candidato na urna eletrônica.
- O sistema gera o registro de voto e deve salvá-lo de acordo com a digitação, utilizando tecnologia Block Chain.
- O eleitor pode conferir seu voto através da tela da urna.
- O registro impresso deve ser gerado a partir do registro salvo e não do digitado para evitar divergências entre a informação que será gravada e a que estará impressa. As informações que deverão ser impressas são: hash de localização do voto na listagem de votos da urna; todos os dados dos candidatos que são apresentados na tela da urna; hash de registro do block chain; e QR Code com todas estas informações.
- O eleitor pode conferir seu voto através do registro impresso.
- O eleitor confirma seu voto e o sistema deve mantê-lo gravado sem quaisquer informações relacionadas ao eleitor (garante o segredo do voto).

### Processo de Cancelamento de Voto para Refazer Votação

- OBS: Ainda não pensei neste processo.

## Validação dos Votos

- Os fiscais partidários e todos os outros interessados podem executar o escrutínio público utilizando o registro impresso do voto.
- O sistema captura o registro impresso do voto através da leitura do QR Code para apresentação dos dados do voto e comparação com o registro impresso. Feita a conferência o sistema irá salvá-lo para a contabilização do Boletim de Urna (BU).
- É feita a conferência de todos os registros dos votos com os registros impressos capturados.
- Todos os presentes serão informadas em caso de existência de problemas na conferência dos votos.

## Criação do Boletim de Urna (BU)

- O sistema totaliza e imprime o BU. O BU deve ser impresso com: o hash final do Block Chain dos votos da urna; com todas as informações do BU; com o hash destas informações do BU; e com o QR Code dos hashes e informações do BU.
- O sistema captura o BU para conferência de dados através da leitura do QR Code.

## Validação do Boletim de Urna (BU)

- É feita a conferência do registro do BU salvo com o registro de BU capturado através do comprovante impresso.
- Todos os presentes serão informadas em caso de existência de problemas na conferência dos BUs.
- Todas as autoridades exigidas pela legislação deverão assinar o BU.

## Criação do Registro de Urna

- O sistema deverá capturar através de escaneamento o BU assinado por todas as autoridades exigidas pela legislação. O sistema deverá persistir esta informação de forma criptografada e compactada.
- O sistema gera o registro de urna com o data e hora do servidor, registro do BU escaneado e registro eletrônico do BU (o qual foi validado no processo anterior). 

## Envio do Registro de Urna

- O sistema compacta, criptografa e envia todas as informações do registro de urna.

## Processamento do Registro de Urna

- O processamento da urna irá capturar o registro de urna e verificar se o hash deste registro é idêntico ao hash do documento escaneado.
- O processamento irá gerar uma hash com as informações capturadas do registro de urna atual e compará-lo com o hash do registro salvo e, somente assim, poderá processá-lo.
- Finalizado o processamento do registro de urna então o sistema salvará o registro de urna juntamente com o hash gerado para sua contabilização juntamente com data e hora automática do servidor.

## Totalização

- A totalização deve ser feita utilizando a tecnologia Block Chain.
