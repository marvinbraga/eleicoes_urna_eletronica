# Processo de Urna Eletrônica
_Por Marcus Vinicius Braga_

## Votação
- Gerar o registro de voto e salvá-lo de acordo com a digitação, utilizando tecnologia Block Chain.
- O eleitor pode conferir seu voto através da tela da urna.
- O registro impresso deve ser gerado a partir do registro salvo e não do digitado.  
- O eleitor pode conferir seu voto através do registro impresso.
- O voto fica gravado sem informações do eleitor (garante o segredo do voto).

### Processo de Cancelamento de Voto para Refazer Votação
- Descrever processo. 

## Validação dos Votos
- O escrutínio público pode ser executado utilizando o registro impresso do voto.
- O registro impresso do voto é capturado para conferência para saber se não foi adulterado.
- É feita a conferência de todos os registros dos votos com os registros impressos capturados.
- Todos os presentes serão informadas em caso de existência de problemas na conferência dos votos.

## Criação do Boletim de Urna (BU)
- O sistema totaliza e imprime o Boletim de Urna (BU + Hash).
- O sistema captura o BU para conferência de dados.

## Validação do Boletim de Urna (BU)
- É feita a conferência do registro do BU salvo com o registro de BU capturado através do comprovante impresso.
- Todos os presentes serão informadas em caso de existência de problemas na conferência dos BUs.

## Criação do Registro de Urna
- O sistema gera o registro de urna (BU + Registro de Votos)

## Envio do Registro de Urna
- O sistema envia o registro de urna.
- Uma cópia assinada do registro de urna deve ser escaneada, criptografada e enviada para que possa haver conferência.   

## Processamento do Registro de Urna
- O processamento da urna irá capturar o registro de urna e verificar se o hash deste registro é identico ao hash do 
  documento escaneado. 
- O processamento irá gerar uma hash com as informações capturadas do registro de urna atual e compará-lo com o 
  hash do registro salvo e, somente assim, poderá processá-lo.
- Finalizado o processamento do registro de urna então o sistema salvará o registro de urna juntamente com 
  o hash gerado para sua contabilização juntamente com data e hora automática do servidor.
  
## Totalização
- A totalização deve ser feita utilizando a tecnologia Block Chain.
  