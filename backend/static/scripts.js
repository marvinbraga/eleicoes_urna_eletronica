$(document).ready(function () {
  // Verificar o status das chaves ao carregar a página
  $.ajax({
    url: BACKEND_URL + '/keys-status',
    type: 'GET',
    success: function (response) {
      if (response.keys_exist) {
        $('#upload-keys').addClass('d-none');
        $('#voting-section').removeClass('d-none');
      } else {
        $('#upload-keys').removeClass('d-none');
        $('#voting-section').addClass('d-none');
      }
    },
    error: function (error) {
      console.error('Erro ao verificar o status das chaves:', error);
    }
  });

  // Enviar chaves de segurança
  $('#key-upload-form').on('submit', function (event) {
    event.preventDefault();

    let cryptographyKey = $('#cryptography_key')[0].files[0];
    let privateKey = $('#private_key')[0].files[0];

    if (!cryptographyKey || !privateKey) {
      alert('Por favor, selecione ambos os arquivos de chave.');
      return;
    }

    let formData = new FormData();
    formData.append('cryptography_key', cryptographyKey);
    formData.append('private_key', privateKey);

    $.ajax({
      url: BACKEND_URL + '/upload-keys',
      type: 'POST',
      data: formData,
      processData: false,
      contentType: false,
      success: function (response) {
        alert('Chaves enviadas com sucesso!');
        $('#upload-keys').addClass('d-none');
        $('#voting-section').removeClass('d-none');
        // Aqui você pode adicionar a lógica para carregar a seção de votação
      },
      error: function (error) {
        alert('Erro ao enviar as chaves. Tente novamente.');
      }
    });
  });

  // Enviar dados da eleição
  $('#eleicao-upload-form').on('submit', function (event) {
    event.preventDefault();

    let eleicaoFile = $('#eleicao_file')[0].files[0];

    if (!eleicaoFile) {
      alert('Por favor, selecione o arquivo JSON da eleição.');
      return;
    }

    let formData = new FormData();
    formData.append('file', eleicaoFile);

    $.ajax({
      url: BACKEND_URL + '/upload-eleicao',
      type: 'POST',
      data: formData,
      processData: false,
      contentType: false,
      success: function (response) {
        alert('Dados da eleição enviados com sucesso!');
        // Aqui você pode adicionar a lógica para inicializar a urna com os dados recebidos
      },
      error: function (error) {
        alert('Erro ao enviar os dados da eleição. Tente novamente.');
      }
    });
  });
});