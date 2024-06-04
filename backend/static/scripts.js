$(document).ready(function () {
  // Verificar o status das chaves ao carregar a página
  $.ajax({
    url: BACKEND_URL + '/keys-status',
    type: 'GET',
    success: function (response) {
      if (response.keys_exist) {
        $('#upload-keys').addClass('d-none');
        $('#voting-section').removeClass('d-none');
        loadCargos();
      } else {
        $('#upload-keys').removeClass('d-none');
        $('#voting-section').addClass('d-none');
      }
    },
    error: function (error) {
      console.error('Erro ao verificar o status das chaves:', error);
    }
  });

  // Enviar chaves de segurança e dados da eleição
  $('#key-upload-form').on('submit', function (event) {
    event.preventDefault();

    let cryptographyKey = $('#cryptography_key')[0].files[0];
    let privateKey = $('#private_key')[0].files[0];
    let electionData = $('#election_data')[0].files[0];

    if (!cryptographyKey || !privateKey || !electionData) {
      alert('Por favor, selecione todos os arquivos necessários.');
      return;
    }

    let formData = new FormData();
    formData.append('cryptography_key', cryptographyKey);
    formData.append('private_key', privateKey);
    formData.append('election_data', electionData);

    $.ajax({
      url: BACKEND_URL + '/upload-keys',
      type: 'POST',
      data: formData,
      processData: false,
      contentType: false,
      success: function (response) {
        alert('Chaves e dados da eleição enviados com sucesso!');
        $('#upload-keys').addClass('d-none');
        $('#voting-section').removeClass('d-none');
        loadCargos();
      },
      error: function (error) {
        alert('Erro ao enviar as chaves e dados da eleição. Tente novamente.');
      }
    });
  });

  // Função para carregar cargos
  function loadCargos() {
    console.log('Carregando cargos...');
    $.ajax({
      url: BACKEND_URL + '/cargos/1', // Supondo que a eleição tenha ID 1
      type: 'GET',
      success: function (response) {
        console.log('Cargos carregados:', response);
        let cargoDropdown = $('#cargo-dropdown');
        cargoDropdown.empty();
        cargoDropdown.append('<option value="">Selecione um cargo</option>'); // Opção padrão
        response.forEach(function (cargo) {
          cargoDropdown.append(`<option value="${cargo.id}">${cargo.nome}</option>`);
        });
      },
      error: function (error) {
        console.error('Erro ao carregar cargos:', error);
      }
    });
  }

  // Mostrar campo para digitar número do candidato ao selecionar um cargo
  $('#cargo-dropdown').on('change', function () {
    if ($(this).val()) {
      $('#candidate-selection').removeClass('d-none');
      $('#candidate-confirmation').addClass('d-none');
      $('#candidate-number').val('');
      $('#candidate-suggestions').empty();
    } else {
      $('#candidate-selection').addClass('d-none');
      $('#candidate-confirmation').addClass('d-none');
    }
  });

  // Buscar candidatos conforme o código é digitado
  $('#candidate-number').on('input', function () {
    let cargoId = $('#cargo-dropdown').val();
    let candidateNumber = $(this).val();

    if (candidateNumber.length > 0) {
      $.ajax({
        url: BACKEND_URL + `/buscar-candidatos/${cargoId}/${candidateNumber}`,
        type: 'GET',
        success: function (response) {
          let suggestions = $('#candidate-suggestions');
          suggestions.empty();
          response.forEach(function (candidate) {
            suggestions.append(`
              <div class="candidate-suggestion" data-id="${candidate.id}">
                <p><strong>Nome:</strong> ${candidate.nome}</p>
                <p><strong>Partido:</strong> ${candidate.partido.sigla}</p>
                <img src="${candidate.foto}" alt="Foto do Candidato" class="img-thumbnail">
              </div>
            `);
          });

          // Adicionar evento de clique nas sugestões
          $('.candidate-suggestion').on('click', function () {
            let candidateId = $(this).data('id');
            let candidate = response.find(c => c.id === candidateId);
            $('#candidate-info').html(`
              <p><strong>Nome:</strong> ${candidate.nome}</p>
              <p><strong>Partido:</strong> ${candidate.partido.sigla}</p>
              <img src="${candidate.foto}" alt="Foto do Candidato" class="img-thumbnail">
            `);
            $('#candidate-confirmation').removeClass('d-none');
          });
        },
        error: function (error) {
          console.error('Erro ao buscar candidatos:', error);
        }
      });
    } else {
      $('#candidate-suggestions').empty();
      $('#candidate-confirmation').addClass('d-none');
    }
  });

  // Confirmar voto
  $('#confirm-vote').on('click', function () {
    let candidateId = $('#candidate-info').find('img').attr('alt').split(' ')[2]; // Pegando o ID do candidato da imagem

    let voto = {
      id: Date.now(), // ID único do voto
      candidato: {id: candidateId},
      hash_localizacao: 'hash_localizacao_placeholder',
      hash_blockchain: 'hash_blockchain_placeholder',
      qr_code: 'qr_code_placeholder'
    };

    $.ajax({
      url: BACKEND_URL + '/votar',
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(voto),
      success: function (response) {
        alert('Voto registrado com sucesso!');
        $('#candidate-confirmation').addClass('d-none');
        $('#candidate-selection').addClass('d-none');
        $('#cargo-dropdown').val('');
      },
      error: function (error) {
        alert('Erro ao registrar o voto. Tente novamente.');
      }
    });
  });
});