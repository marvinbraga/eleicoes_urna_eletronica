$(document).ready(function () {
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
});