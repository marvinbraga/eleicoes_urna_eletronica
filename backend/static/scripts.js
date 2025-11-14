$(document).ready(function () {
  // Variável global para armazenar o candidato selecionado
  let selectedCandidate = null;

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
            selectedCandidate = response.find(c => c.id === candidateId);
            $('#candidate-info').html(`
              <p><strong>Nome:</strong> ${selectedCandidate.nome}</p>
              <p><strong>Partido:</strong> ${selectedCandidate.partido.sigla}</p>
              <p><strong>Código:</strong> ${selectedCandidate.codigo}</p>
              <img src="${selectedCandidate.foto}" alt="Foto do Candidato ${selectedCandidate.nome}" class="img-thumbnail">
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
    if (!selectedCandidate) {
      alert('Por favor, selecione um candidato antes de confirmar o voto.');
      return;
    }

    let voto = {
      candidato: selectedCandidate
    };

    $.ajax({
      url: BACKEND_URL + '/votar',
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(voto),
      success: function (response) {
        if (response.voto) {
          // Exibir recibo do voto
          showVoteReceipt(response.voto);
        } else {
          alert('Voto registrado com sucesso!');
        }
        // Resetar seleção
        selectedCandidate = null;
        $('#candidate-confirmation').addClass('d-none');
        $('#candidate-selection').addClass('d-none');
        $('#cargo-dropdown').val('');
        $('#candidate-number').val('');
      },
      error: function (error) {
        console.error('Erro ao registrar o voto:', error);
        alert('Erro ao registrar o voto. Tente novamente.');
      }
    });
  });

  // Função para exibir recibo do voto
  function showVoteReceipt(voto) {
    let receiptHtml = `
      <div class="alert alert-success mt-3">
        <h4>Voto Registrado com Sucesso!</h4>
        <p><strong>ID do Voto:</strong> ${voto.id}</p>
        <p><strong>Candidato:</strong> ${voto.candidato.nome}</p>
        <p><strong>Partido:</strong> ${voto.candidato.partido.sigla}</p>
        <p><strong>Código:</strong> ${voto.candidato.codigo}</p>
        <p><strong>Data/Hora:</strong> ${new Date(voto.data_hora).toLocaleString('pt-BR')}</p>
        <div class="text-center mt-3">
          <img src="${voto.qr_code}" alt="QR Code do Voto" style="max-width: 200px;">
          <p><small>Escaneie este QR Code para validar seu voto</small></p>
        </div>
      </div>
    `;
    $('#candidate-info').html(receiptHtml);

    // Auto-ocultar após 10 segundos
    setTimeout(function() {
      $('#candidate-confirmation').addClass('d-none');
    }, 10000);
  }

  // Totalizar votos
  $('#btn-totalizar').on('click', function () {
    $.ajax({
      url: BACKEND_URL + '/totalizar-votos/1',
      type: 'GET',
      success: function (response) {
        console.log('Totalização:', response);
        let resultsHtml = `
          <div class="card">
            <div class="card-header bg-info text-white">
              <h5>Totalização de Votos</h5>
            </div>
            <div class="card-body">
              <p><strong>Data/Hora:</strong> ${new Date(response.data_hora).toLocaleString('pt-BR')}</p>
              <p><strong>Hash Blockchain:</strong> <code>${response.hash_blockchain}</code></p>
              <p><strong>Total de Votos:</strong> ${response.votos_totalizados.length}</p>
              <h6 class="mt-3">Votos por Candidato:</h6>
              <table class="table table-striped">
                <thead>
                  <tr>
                    <th>Candidato</th>
                    <th>Partido</th>
                    <th>Votos</th>
                  </tr>
                </thead>
                <tbody>
        `;

        // Contar votos por candidato
        let voteCounts = {};
        response.votos_totalizados.forEach(function(voto) {
          let candidatoId = voto.candidato.id;
          if (!voteCounts[candidatoId]) {
            voteCounts[candidatoId] = {
              nome: voto.candidato.nome,
              partido: voto.candidato.partido.sigla,
              count: 0
            };
          }
          voteCounts[candidatoId].count++;
        });

        // Ordenar por quantidade de votos
        let sortedCandidates = Object.values(voteCounts).sort((a, b) => b.count - a.count);

        sortedCandidates.forEach(function(candidato) {
          resultsHtml += `
            <tr>
              <td>${candidato.nome}</td>
              <td>${candidato.partido}</td>
              <td><strong>${candidato.count}</strong></td>
            </tr>
          `;
        });

        resultsHtml += `
                </tbody>
              </table>
              <div class="alert alert-success mt-3">
                <strong>Assinatura Digital Verificada:</strong> ${response.assinatura ? '✓ Válida' : '✗ Não disponível'}
              </div>
            </div>
          </div>
        `;
        $('#results-display').html(resultsHtml);
      },
      error: function (error) {
        console.error('Erro ao totalizar votos:', error);
        alert('Erro ao totalizar votos. Verifique se há votos registrados.');
      }
    });
  });

  // Gerar Boletim de Urna
  $('#btn-boletim').on('click', function () {
    $.ajax({
      url: BACKEND_URL + '/gerar-boletim-urna',
      type: 'GET',
      success: function (response) {
        console.log('Boletim de Urna:', response);
        let boletimHtml = `
          <div class="card">
            <div class="card-header bg-warning">
              <h5>Boletim de Urna</h5>
            </div>
            <div class="card-body">
              <div class="row">
                <div class="col-md-6">
                  <p><strong>ID:</strong> ${response.id}</p>
                  <p><strong>Seção:</strong> ${response.secao}</p>
                  <p><strong>Zona:</strong> ${response.zona}</p>
                  <p><strong>Município:</strong> ${response.municipio}</p>
                  <p><strong>Estado:</strong> ${response.estado}</p>
                </div>
                <div class="col-md-6">
                  <p><strong>Data/Hora:</strong> ${new Date(response.data_hora).toLocaleString('pt-BR')}</p>
                  <p><strong>Total de Votos:</strong> ${response.votos.length}</p>
                  <p><strong>Hash Final Blockchain:</strong></p>
                  <code class="d-block">${response.hash_final_blockchain}</code>
                </div>
              </div>
              <div class="alert alert-success mt-3">
                <strong>Assinatura Digital:</strong> ${response.assinatura ? '✓ Boletim assinado e verificado' : '✗ Não disponível'}
              </div>
              <div class="alert alert-info">
                <strong>Hash do BU:</strong> <code>${response.hash_bu}</code>
              </div>
            </div>
          </div>
        `;
        $('#results-display').html(boletimHtml);
      },
      error: function (error) {
        console.error('Erro ao gerar boletim de urna:', error);
        alert('Erro ao gerar boletim de urna. Verifique se há votos registrados.');
      }
    });
  });
});