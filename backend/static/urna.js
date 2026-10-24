$(document).ready(function () {
    // Estado da aplicação
    let appState = {
        eleicao: null,
        cargos: [],
        cargoAtual: null,
        candidatos: [],
        numeroDigitado: '',
        candidatoSelecionado: null,
        votosBranco: 0,
        votosNulo: 0,
        votosValidos: 0,
        votosConfirmadosNoCargo: 0,
        candidatosJaVotados: [],
        fase: 'upload' // upload, selecao-cargo, digitacao, confirmacao, fim
    };

    // Quantidade de dígitos do número na urna (padrão TSE). O cargo pode trazer numero_digitos.
    const DIGITOS_POR_CARGO = {
        'presidente': 2,
        'governador': 2,
        'senador': 3,
        'deputado federal': 4,
        'deputado estadual': 5,
        'deputado distrital': 5,
        'prefeito': 2,
        'vereador': 5
    };

    function digitosDoCargo(cargo) {
        const informado = Number(cargo && cargo.numero_digitos);
        if (Number.isInteger(informado) && informado > 0) {
            return informado;
        }
        const nome = (cargo && cargo.nome ? cargo.nome : '').trim().toLowerCase();
        return DIGITOS_POR_CARGO[nome] || 5;
    }

    // Quantos candidatos o eleitor escolhe. No Senado da última eleição são 2.
    const VOTOS_POR_CARGO = {
        'presidente': 1,
        'governador': 1,
        'senador': 2,
        'deputado federal': 1,
        'deputado estadual': 1,
        'deputado distrital': 1,
        'prefeito': 1,
        'vereador': 1
    };

    function votosDoCargo(cargo) {
        const informado = Number(cargo && cargo.votos_por_eleitor);
        if (Number.isInteger(informado) && informado > 0) {
            return informado;
        }
        const nome = (cargo && cargo.nome ? cargo.nome : '').trim().toLowerCase();
        return VOTOS_POR_CARGO[nome] || 1;
    }

    // Sons (simulados com beep)
    const playBeep = () => {
        // Feedback sonoro simulado
        console.log('Beep!');
    };

    // Inicialização
    verificarStatusChaves();

    // Verificar se as chaves já foram carregadas
    function verificarStatusChaves() {
        $.ajax({
            url: BACKEND_URL + '/keys-status',
            type: 'GET',
            success: function (response) {
                if (response.keys_exist) {
                    $('#upload-keys').addClass('d-none');
                    $('#urna-container').removeClass('d-none');
                    carregarCargos();
                } else {
                    $('#upload-keys').removeClass('d-none');
                    $('#urna-container').addClass('d-none');
                }
            },
            error: function (error) {
                console.error('Erro ao verificar status das chaves:', error);
                mostrarErro('Erro ao conectar com o servidor');
            }
        });
    }

    // Upload de chaves
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

        mostrarLoading('Inicializando urna...');

        $.ajax({
            url: BACKEND_URL + '/upload-keys',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                mostrarFeedback('Urna inicializada com sucesso!', 'success');
                setTimeout(() => {
                    $('#upload-keys').addClass('d-none');
                    $('#urna-container').removeClass('d-none');
                    carregarCargos();
                }, 1500);
            },
            error: function (error) {
                console.error('Erro ao enviar chaves:', error);
                mostrarErro('Erro ao inicializar urna. Verifique os arquivos.');
            }
        });
    });

    // Carregar cargos
    function carregarCargos() {
        mostrarLoading('Carregando cargos...');

        $.ajax({
            url: BACKEND_URL + '/cargos/1',
            type: 'GET',
            success: function (cargos) {
                appState.cargos = cargos;
                if (cargos.length > 0) {
                    mostrarSelecaoCargo();
                } else {
                    mostrarErro('Nenhum cargo disponível para votação');
                }
            },
            error: function (error) {
                console.error('Erro ao carregar cargos:', error);
                mostrarErro('Erro ao carregar cargos');
            }
        });
    }

    // Mostrar tela de seleção de cargo
    function mostrarSelecaoCargo() {
        appState.fase = 'selecao-cargo';

        let html = `
            <div class="tela-cargo fade-in">
                <h3>SEU VOTO PARA</h3>
                <div class="instrucao">
                    <i class="fas fa-info-circle"></i>
                    Selecione o cargo para o qual deseja votar
                </div>
        `;

        appState.cargos.forEach((cargo, index) => {
            const votos = votosDoCargo(cargo);
            const digitos = digitosDoCargo(cargo);
            const detalhe = votos > 1
                ? `${votos} candidatos (${digitos} dígitos cada)`
                : `1 candidato (${digitos} dígitos)`;
            html += `
                <div class="cargo-option" data-cargo-id="${cargo.id}" data-index="${index}">
                    <h4>${cargo.nome}</h4>
                    <p class="mb-0">${detalhe}</p>
                </div>
            `;
        });

        html += '</div>';

        $('#display-content').html(html);

        // Adicionar evento de clique
        $('.cargo-option').on('click', function() {
            const cargoId = $(this).data('cargo-id');
            const index = $(this).data('index');
            selecionarCargo(appState.cargos[index]);
            playBeep();
        });
    }

    // Selecionar cargo e iniciar votação
    function selecionarCargo(cargo) {
        appState.cargoAtual = cargo;
        appState.numeroDigitado = '';
        appState.candidatoSelecionado = null;
        appState.votosConfirmadosNoCargo = 0;
        appState.candidatosJaVotados = [];
        appState.fase = 'digitacao';

        mostrarTelaDigitacao();
    }

    // Mostrar tela de digitação
    function mostrarTelaDigitacao() {
        const digitosNecessarios = digitosDoCargo(appState.cargoAtual);
        const totalVotos = votosDoCargo(appState.cargoAtual);
        const ordem = appState.votosConfirmadosNoCargo + 1;
        const progresso = totalVotos > 1 ? `Voto ${ordem} de ${totalVotos}. ` : '';

        let html = `
            <div class="tela-votacao fade-in">
                <h3>SEU VOTO PARA</h3>
                <h2 style="color: #1e3a8a; font-weight: bold;">${appState.cargoAtual.nome.toUpperCase()}</h2>

                <div class="instrucao">
                    <i class="fas fa-keyboard"></i>
                    ${progresso}Digite o número do candidato (${digitosNecessarios} dígitos)
                </div>

                <div class="numero-display">
        `;

        for (let i = 0; i < digitosNecessarios; i++) {
            const digito = appState.numeroDigitado[i] || '';
            const isActive = i === appState.numeroDigitado.length;
            html += `<div class="digito-box ${isActive ? 'active' : ''}">${digito}</div>`;
        }

        html += `
                </div>

                <div id="candidato-preview">
                    <!-- Informações do candidato aparecerão aqui -->
                </div>
            </div>
        `;

        $('#display-content').html(html);
    }

    // Eventos do teclado numérico
    $('.key-number').on('click', function() {
        const numero = $(this).data('number').toString();
        digitarNumero(numero);
        playBeep();
    });

    function digitarNumero(numero) {
        if (appState.fase !== 'digitacao') return;

        const digitosNecessarios = digitosDoCargo(appState.cargoAtual);

        if (appState.numeroDigitado.length < digitosNecessarios) {
            appState.numeroDigitado += numero;
            mostrarTelaDigitacao();

            // Buscar candidato quando completar os dígitos
            if (appState.numeroDigitado.length === digitosNecessarios) {
                buscarCandidato(appState.numeroDigitado);
            }
        }
    }

    // Buscar candidato
    function buscarCandidato(codigo) {
        $.ajax({
            url: BACKEND_URL + `/buscar-candidatos/${appState.cargoAtual.id}/${codigo}`,
            type: 'GET',
            success: function (candidatos) {
                if (candidatos && candidatos.length > 0) {
                    if (appState.candidatosJaVotados.indexOf(candidatos[0].id) !== -1) {
                        appState.candidatoSelecionado = null;
                        mostrarCandidatoRepetido(candidatos[0]);
                        return;
                    }
                    appState.candidatoSelecionado = candidatos[0];
                    mostrarCandidato(candidatos[0]);
                } else {
                    mostrarVotoNulo();
                }
            },
            error: function (error) {
                console.error('Erro ao buscar candidato:', error);
                mostrarVotoNulo();
            }
        });
    }

    // Mostrar informações do candidato
    function mostrarCandidato(candidato) {
        let html = `
            <div class="candidato-info fade-in">
                <div class="candidato-header">
                    <img src="${candidato.foto}" alt="${candidato.nome}" class="candidato-foto">
                    <div class="candidato-dados">
                        <h4>${candidato.nome}</h4>
                        <div class="partido">${candidato.partido.sigla} - ${candidato.partido.nome}</div>
                        <div class="numero">Número: ${candidato.codigo}</div>
                    </div>
                </div>
                <div class="instrucao mt-3">
                    <i class="fas fa-check-circle"></i>
                    Confira os dados e pressione CONFIRMA para votar ou CORRIGE para voltar
                </div>
            </div>
        `;

        $('#candidato-preview').html(html);
        appState.fase = 'confirmacao';
    }

    function mostrarCandidatoRepetido(candidato) {
        let html = `
            <div class="voto-nulo fade-in">
                <h4>CANDIDATO JÁ ESCOLHIDO</h4>
                <p>${candidato.nome} já recebeu um voto seu para ${appState.cargoAtual.nome}</p>
                <div class="instrucao mt-3">
                    <i class="fas fa-exclamation-triangle"></i>
                    Pressione CORRIGE e vote em outro candidato
                </div>
            </div>
        `;

        $('#candidato-preview').html(html);
        appState.fase = 'digitacao';
    }

    // Mostrar voto nulo
    function mostrarVotoNulo() {
        let html = `
            <div class="voto-nulo fade-in">
                <h4>NÚMERO ERRADO</h4>
                <p>Não existe candidato com este número</p>
                <p><strong>Seu voto será NULO</strong></p>
                <div class="instrucao mt-3">
                    <i class="fas fa-exclamation-triangle"></i>
                    Pressione CONFIRMA para votar NULO ou CORRIGE para digitar novamente
                </div>
            </div>
        `;

        $('#candidato-preview').html(html);
        appState.candidatoSelecionado = null;
        appState.fase = 'confirmacao';
    }

    // Botão BRANCO
    $('#btn-branco').on('click', function() {
        if (appState.fase === 'digitacao') {
            appState.numeroDigitado = '';
            appState.candidatoSelecionado = null;
            mostrarVotoBranco();
            playBeep();
        }
    });

    function mostrarVotoBranco() {
        appState.fase = 'confirmacao';

        let html = `
            <div class="mensagem-voto branco fade-in">
                <i class="fas fa-file"></i>
                <h3>VOTO EM BRANCO</h3>
                <p>Você escolheu votar em branco</p>
                <div class="instrucao mt-3">
                    <i class="fas fa-check-circle"></i>
                    Pressione CONFIRMA para votar em BRANCO ou CORRIGE para voltar
                </div>
            </div>
        `;

        $('#display-content').html(html);
    }

    // Botão CORRIGE
    $('#btn-corrige').on('click', function() {
        if (appState.fase === 'digitacao' || appState.fase === 'confirmacao') {
            corrigir();
            playBeep();
        }
    });

    function corrigir() {
        appState.numeroDigitado = '';
        appState.candidatoSelecionado = null;
        appState.fase = 'digitacao';
        mostrarTelaDigitacao();
    }

    // Botão CONFIRMA
    $('#btn-confirma').on('click', function() {
        if (appState.fase === 'confirmacao') {
            confirmarVoto();
            playBeep();
        }
    });

    function confirmarVoto() {
        mostrarLoading('Registrando voto...');

        let voto = {
            candidato: appState.candidatoSelecionado
        };

        $.ajax({
            url: BACKEND_URL + '/votar',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(voto),
            success: function (response) {
                if (appState.candidatoSelecionado) {
                    appState.candidatosJaVotados.push(appState.candidatoSelecionado.id);
                    appState.votosValidos++;
                } else if (appState.numeroDigitado === '') {
                    appState.votosBranco++;
                } else {
                    appState.votosNulo++;
                }

                appState.votosConfirmadosNoCargo++;
                atualizarStatusVotos();

                const aindaFalta = appState.votosConfirmadosNoCargo < votosDoCargo(appState.cargoAtual);
                mostrarMensagemSucesso(aindaFalta);

                setTimeout(() => {
                    if (aindaFalta) {
                        appState.numeroDigitado = '';
                        appState.candidatoSelecionado = null;
                        appState.fase = 'digitacao';
                        mostrarTelaDigitacao();
                    } else {
                        proximoCargo();
                    }
                }, aindaFalta ? 1500 : 3000);
            },
            error: function (error) {
                console.error('Erro ao registrar voto:', error);
                mostrarErro('Erro ao registrar voto. Tente novamente.');
                setTimeout(() => {
                    mostrarTelaDigitacao();
                }, 2000);
            }
        });
    }

    function mostrarMensagemSucesso(proximoNoMesmoCargo) {
        const totalVotos = votosDoCargo(appState.cargoAtual);
        const titulo = totalVotos > 1
            ? `VOTO ${appState.votosConfirmadosNoCargo} DE ${totalVotos} CONFIRMADO`
            : 'VOTO CONFIRMADO';
        const texto = proximoNoMesmoCargo
            ? 'Digite o número do próximo candidato'
            : 'Seu voto foi registrado com segurança';
        let html = `
            <div class="mensagem-voto sucesso fade-in">
                <i class="fas fa-check-circle"></i>
                <h3>${titulo}</h3>
                <p>${texto}</p>
            </div>
        `;

        $('#display-content').html(html);
    }

    function proximoCargo() {
        const indexAtual = appState.cargos.findIndex(c => c.id === appState.cargoAtual.id);

        if (indexAtual < appState.cargos.length - 1) {
            selecionarCargo(appState.cargos[indexAtual + 1]);
        } else {
            mostrarFimVotacao();
        }
    }

    function mostrarFimVotacao() {
        appState.fase = 'fim';

        let html = `
            <div class="mensagem-voto sucesso fade-in">
                <i class="fas fa-vote-yea"></i>
                <h3>FIM</h3>
                <p>Votação concluída com sucesso!</p>
                <div class="mt-4">
                    <button class="btn btn-primary btn-lg" onclick="location.reload()">
                        <i class="fas fa-redo"></i> Nova Votação
                    </button>
                </div>
            </div>
        `;

        $('#display-content').html(html);
    }

    function atualizarStatusVotos() {
        const total = appState.votosValidos + appState.votosBranco + appState.votosNulo;
        $('#status-votes').text(`${total} votos`);
    }

    // Funções auxiliares
    function mostrarLoading(mensagem) {
        let html = `
            <div class="loading">
                <i class="fas fa-spinner"></i>
                <h4 class="mt-3">${mensagem}</h4>
            </div>
        `;
        $('#display-content').html(html);
    }

    function mostrarErro(mensagem) {
        let html = `
            <div class="text-center py-5">
                <i class="fas fa-exclamation-triangle" style="font-size: 3rem; color: #ef4444;"></i>
                <h3 class="mt-3" style="color: #dc2626;">Erro</h3>
                <p>${mensagem}</p>
            </div>
        `;
        $('#display-content').html(html);
    }

    function mostrarFeedback(mensagem, tipo) {
        const icone = tipo === 'success' ? 'check-circle' : 'exclamation-circle';
        const cor = tipo === 'success' ? '#10b981' : '#ef4444';

        let html = `
            <i class="fas fa-${icone}" style="font-size: 4rem; color: ${cor};"></i>
            <h3 class="mt-3">${mensagem}</h3>
        `;

        $('#feedback-content').html(html);
        $('#feedbackModal').modal('show');

        setTimeout(() => {
            $('#feedbackModal').modal('hide');
        }, 2000);
    }

    // Suporte a teclado físico
    $(document).on('keydown', function(e) {
        if (appState.fase !== 'digitacao' && appState.fase !== 'confirmacao') return;

        // Números 0-9
        if (e.key >= '0' && e.key <= '9') {
            digitarNumero(e.key);
            playBeep();
        }
        // Enter = CONFIRMA
        else if (e.key === 'Enter' && appState.fase === 'confirmacao') {
            confirmarVoto();
            playBeep();
        }
        // Backspace = CORRIGE
        else if (e.key === 'Backspace') {
            e.preventDefault();
            corrigir();
            playBeep();
        }
        // Espaço = BRANCO
        else if (e.key === ' ' && appState.fase === 'digitacao') {
            e.preventDefault();
            mostrarVotoBranco();
            playBeep();
        }
    });
});
