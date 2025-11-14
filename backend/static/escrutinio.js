$(document).ready(function () {
    // Estado da aplicação
    let appState = {
        totalizacao: null,
        boletim: null,
        autoRefresh: false,
        refreshInterval: null,
        charts: {
            distribuicao: null,
            candidatos: null
        }
    };

    // Inicialização
    inicializar();

    function inicializar() {
        // Tentar carregar resultados existentes
        tentarCarregarResultados();
    }

    function tentarCarregarResultados() {
        $.ajax({
            url: BACKEND_URL + '/totalizar-votos/1',
            type: 'GET',
            success: function (response) {
                processarTotalizacao(response);
            },
            error: function (error) {
                console.log('Nenhum resultado disponível ainda');
            }
        });
    }

    // Botão Totalizar Votos
    $('#btn-totalizar').on('click', function () {
        totalizarVotos();
    });

    function totalizarVotos() {
        mostrarLoading('Totalizando votos...');

        $.ajax({
            url: BACKEND_URL + '/totalizar-votos/1',
            type: 'GET',
            success: function (response) {
                console.log('Totalização:', response);
                processarTotalizacao(response);
                $('#loadingModal').modal('hide');
                mostrarNotificacao('Totalização concluída com sucesso!', 'success');
            },
            error: function (error) {
                console.error('Erro ao totalizar votos:', error);
                $('#loadingModal').modal('hide');
                mostrarNotificacao('Erro ao totalizar votos. Verifique se há votos registrados.', 'error');
            }
        });
    }

    // Processar totalização
    function processarTotalizacao(totalizacao) {
        appState.totalizacao = totalizacao;
        atualizarUltimaAtualizacao();

        // Processar dados
        const dados = processarDados(totalizacao);

        // Atualizar estatísticas
        atualizarEstatisticas(dados);

        // Atualizar resultados por cargo
        exibirResultadosCargos(dados);

        // Atualizar gráficos
        atualizarGraficos(dados);

        // Atualizar auditoria
        atualizarAuditoria(totalizacao);

        // Mostrar containers
        $('#graficos-container').fadeIn();
    }

    // Processar dados da totalização
    function processarDados(totalizacao) {
        let dados = {
            totalVotos: totalizacao.votos_totalizados.length,
            votosValidos: 0,
            votosBrancos: 0,
            votosNulos: 0,
            candidatos: {},
            cargos: {}
        };

        totalizacao.votos_totalizados.forEach(voto => {
            if (voto.candidato) {
                dados.votosValidos++;

                const candidatoId = voto.candidato.id;
                const cargoId = voto.candidato.cargo_id;

                // Contagem por candidato
                if (!dados.candidatos[candidatoId]) {
                    dados.candidatos[candidatoId] = {
                        info: voto.candidato,
                        votos: 0
                    };
                }
                dados.candidatos[candidatoId].votos++;

                // Contagem por cargo
                if (!dados.cargos[cargoId]) {
                    dados.cargos[cargoId] = {
                        nome: voto.candidato.cargo?.nome || 'Cargo',
                        candidatos: {}
                    };
                }
                if (!dados.cargos[cargoId].candidatos[candidatoId]) {
                    dados.cargos[cargoId].candidatos[candidatoId] = {
                        info: voto.candidato,
                        votos: 0
                    };
                }
                dados.cargos[cargoId].candidatos[candidatoId].votos++;
            }
        });

        return dados;
    }

    // Atualizar estatísticas
    function atualizarEstatisticas(dados) {
        animarNumero($('#total-votos'), dados.totalVotos);
        animarNumero($('#votos-validos'), dados.votosValidos);
        animarNumero($('#votos-brancos'), dados.votosBrancos);
        animarNumero($('#votos-nulos'), dados.votosNulos);
    }

    function animarNumero(elemento, valorFinal) {
        const valorAtual = parseInt(elemento.text()) || 0;
        const duracao = 1000;
        const passos = 30;
        const incremento = (valorFinal - valorAtual) / passos;
        let contador = 0;

        const intervalo = setInterval(() => {
            contador++;
            const novoValor = Math.round(valorAtual + (incremento * contador));
            elemento.text(novoValor);

            if (contador >= passos) {
                clearInterval(intervalo);
                elemento.text(valorFinal);
            }
        }, duracao / passos);
    }

    // Exibir resultados por cargo
    function exibirResultadosCargos(dados) {
        let html = '';

        Object.keys(dados.cargos).forEach(cargoId => {
            const cargo = dados.cargos[cargoId];

            html += `
                <div class="resultado-cargo fade-in-up">
                    <h5><i class="fas fa-award"></i> ${cargo.nome}</h5>
            `;

            // Ordenar candidatos por votos
            const candidatosOrdenados = Object.values(cargo.candidatos)
                .sort((a, b) => b.votos - a.votos);

            const totalVotosCargo = candidatosOrdenados.reduce((sum, c) => sum + c.votos, 0);

            candidatosOrdenados.forEach((candidato, index) => {
                const percentual = totalVotosCargo > 0
                    ? ((candidato.votos / totalVotosCargo) * 100).toFixed(2)
                    : 0;

                let classeDestaque = '';
                let medalha = '';

                if (index === 0) {
                    classeDestaque = 'primeiro vencedor';
                    medalha = '<span class="medalha medalha-ouro">🥇</span>';
                } else if (index === 1) {
                    classeDestaque = 'segundo';
                    medalha = '<span class="medalha medalha-prata">🥈</span>';
                } else if (index === 2) {
                    classeDestaque = 'terceiro';
                    medalha = '<span class="medalha medalha-bronze">🥉</span>';
                }

                html += `
                    <div class="candidato-resultado ${classeDestaque}">
                        <div class="posicao-badge">
                            ${medalha || (index + 1) + 'º'}
                        </div>
                        ${candidato.info.foto ? `
                            <img src="${candidato.info.foto}" alt="${candidato.info.nome}"
                                 class="candidato-foto-mini">
                        ` : ''}
                        <div class="candidato-info-resultado">
                            <h6>${candidato.info.nome}</h6>
                            <div class="partido-info">
                                ${candidato.info.partido?.sigla || 'N/A'} -
                                ${candidato.info.partido?.nome || 'Partido'}
                            </div>
                            <div class="barra-progresso-container">
                                <div class="barra-progresso" style="width: ${percentual}%"></div>
                            </div>
                        </div>
                        <div class="votos-info">
                            <div class="votos-numero count-up">${candidato.votos}</div>
                            <div class="votos-percentual">${percentual}%</div>
                        </div>
                    </div>
                `;
            });

            html += '</div>';
        });

        if (html === '') {
            html = `
                <div class="text-center py-5">
                    <i class="fas fa-inbox" style="font-size: 4rem; color: #cbd5e0;"></i>
                    <h4 class="mt-3 text-muted">Nenhum resultado disponível</h4>
                </div>
            `;
        }

        $('#resultados-cargos').html(html);
    }

    // Atualizar gráficos
    function atualizarGraficos(dados) {
        // Gráfico de distribuição
        atualizarGraficoDistribuicao(dados);

        // Gráfico de candidatos
        atualizarGraficoCandidatos(dados);
    }

    function atualizarGraficoDistribuicao(dados) {
        const ctx = document.getElementById('chart-distribuicao').getContext('2d');

        if (appState.charts.distribuicao) {
            appState.charts.distribuicao.destroy();
        }

        appState.charts.distribuicao = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Votos Válidos', 'Votos em Branco', 'Votos Nulos'],
                datasets: [{
                    data: [dados.votosValidos, dados.votosBrancos, dados.votosNulos],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(148, 163, 184, 0.8)',
                        'rgba(239, 68, 68, 0.8)'
                    ],
                    borderColor: [
                        'rgb(16, 185, 129)',
                        'rgb(148, 163, 184)',
                        'rgb(239, 68, 68)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 14
                            },
                            padding: 20
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = dados.totalVotos;
                                const valor = context.parsed;
                                const percentual = total > 0 ? ((valor / total) * 100).toFixed(2) : 0;
                                return `${context.label}: ${valor} (${percentual}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    function atualizarGraficoCandidatos(dados) {
        const ctx = document.getElementById('chart-candidatos').getContext('2d');

        if (appState.charts.candidatos) {
            appState.charts.candidatos.destroy();
        }

        // Pegar top 10 candidatos
        const candidatosOrdenados = Object.values(dados.candidatos)
            .sort((a, b) => b.votos - a.votos)
            .slice(0, 10);

        const labels = candidatosOrdenados.map(c => c.info.nome);
        const votos = candidatosOrdenados.map(c => c.votos);

        // Gerar cores dinâmicas
        const cores = candidatosOrdenados.map((_, index) => {
            const hue = (index * 360 / candidatosOrdenados.length);
            return `hsla(${hue}, 70%, 60%, 0.8)`;
        });

        appState.charts.candidatos = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Votos',
                    data: votos,
                    backgroundColor: cores,
                    borderColor: cores.map(c => c.replace('0.8', '1')),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Votos: ${context.parsed.y}`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Atualizar auditoria
    function atualizarAuditoria(totalizacao) {
        if (totalizacao.hash_blockchain) {
            $('#blockchain-status')
                .removeClass('badge-secondary')
                .addClass('badge-success')
                .html('<i class="fas fa-check-circle"></i> Verificado');

            $('#blockchain-hash').show();
            $('#hash-value').text(totalizacao.hash_blockchain);
        }

        if (totalizacao.assinatura) {
            $('#signature-status')
                .removeClass('badge-secondary')
                .addClass('badge-success')
                .html('<i class="fas fa-check-circle"></i> Verificada');

            $('#signature-info').show();
        }
    }

    // Botão Atualizar
    $('#btn-atualizar').on('click', function () {
        totalizarVotos();
    });

    // Auto-refresh
    $('#auto-refresh').on('change', function () {
        appState.autoRefresh = $(this).is(':checked');

        if (appState.autoRefresh) {
            appState.refreshInterval = setInterval(() => {
                totalizarVotos();
            }, 5000);
            mostrarNotificacao('Atualização automática ativada', 'info');
        } else {
            if (appState.refreshInterval) {
                clearInterval(appState.refreshInterval);
                appState.refreshInterval = null;
            }
            mostrarNotificacao('Atualização automática desativada', 'info');
        }
    });

    // Botão Boletim de Urna
    $('#btn-boletim').on('click', function () {
        gerarBoletimUrna();
    });

    function gerarBoletimUrna() {
        mostrarLoading('Gerando Boletim de Urna...');

        $.ajax({
            url: BACKEND_URL + '/gerar-boletim-urna',
            type: 'GET',
            success: function (response) {
                console.log('Boletim de Urna:', response);
                appState.boletim = response;
                exibirBoletimUrna(response);
                $('#loadingModal').modal('hide');
                mostrarNotificacao('Boletim de Urna gerado com sucesso!', 'success');
            },
            error: function (error) {
                console.error('Erro ao gerar boletim:', error);
                $('#loadingModal').modal('hide');
                mostrarNotificacao('Erro ao gerar boletim. Verifique se há votos registrados.', 'error');
            }
        });
    }

    function exibirBoletimUrna(boletim) {
        let html = `
            <div class="boletim-header">
                <h3>BOLETIM DE URNA OFICIAL</h3>
                <p class="mb-0">Documento Oficial com Assinatura Digital</p>
            </div>

            <div class="boletim-info-grid">
                <div class="boletim-info-item">
                    <label><i class="fas fa-fingerprint"></i> ID do Boletim</label>
                    <div class="value">${boletim.id}</div>
                </div>
                <div class="boletim-info-item">
                    <label><i class="fas fa-map-marker-alt"></i> Seção</label>
                    <div class="value">${boletim.secao}</div>
                </div>
                <div class="boletim-info-item">
                    <label><i class="fas fa-location-arrow"></i> Zona</label>
                    <div class="value">${boletim.zona}</div>
                </div>
                <div class="boletim-info-item">
                    <label><i class="fas fa-city"></i> Município</label>
                    <div class="value">${boletim.municipio}</div>
                </div>
                <div class="boletim-info-item">
                    <label><i class="fas fa-flag"></i> Estado</label>
                    <div class="value">${boletim.estado}</div>
                </div>
                <div class="boletim-info-item">
                    <label><i class="fas fa-clock"></i> Data/Hora</label>
                    <div class="value">${new Date(boletim.data_hora).toLocaleString('pt-BR')}</div>
                </div>
            </div>

            <div class="mt-4">
                <h6><i class="fas fa-vote-yea"></i> Total de Votos</h6>
                <div class="alert alert-info">
                    <h4 class="mb-0">${boletim.votos.length} votos registrados</h4>
                </div>
            </div>

            <div class="mt-4">
                <h6><i class="fas fa-link"></i> Hash Final Blockchain</h6>
                <div class="code-box">
                    <code>${boletim.hash_final_blockchain}</code>
                </div>
            </div>

            <div class="mt-4">
                <h6><i class="fas fa-shield-alt"></i> Hash do Boletim de Urna</h6>
                <div class="code-box">
                    <code>${boletim.hash_bu}</code>
                </div>
            </div>

            <div class="alert alert-success mt-4">
                <h5><i class="fas fa-certificate"></i> Certificação</h5>
                <p class="mb-0">
                    ${boletim.assinatura ?
                        '✓ Este boletim possui assinatura digital válida e foi verificado com sucesso.' :
                        '✗ Assinatura digital não disponível'}
                </p>
            </div>
        `;

        $('#boletim-content').html(html);
        $('#boletim-container').fadeIn();

        // Scroll suave até o boletim
        $('html, body').animate({
            scrollTop: $('#boletim-container').offset().top - 100
        }, 1000);
    }

    // Funções auxiliares
    function mostrarLoading(mensagem) {
        $('#loading-message').text(mensagem);
        $('#loadingModal').modal('show');
    }

    function atualizarUltimaAtualizacao() {
        const agora = new Date();
        $('#ultima-atualizacao').text(agora.toLocaleTimeString('pt-BR'));
    }

    function mostrarNotificacao(mensagem, tipo) {
        const icone = tipo === 'success' ? 'check-circle' :
                     tipo === 'error' ? 'exclamation-circle' :
                     'info-circle';
        const cor = tipo === 'success' ? 'success' :
                   tipo === 'error' ? 'danger' :
                   'info';

        const html = `
            <div class="alert alert-${cor} alert-dismissible fade show position-fixed"
                 style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;" role="alert">
                <i class="fas fa-${icone}"></i> ${mensagem}
                <button type="button" class="close" data-dismiss="alert">
                    <span>&times;</span>
                </button>
            </div>
        `;

        $('body').append(html);

        setTimeout(() => {
            $('.alert').fadeOut(() => {
                $(this).remove();
            });
        }, 5000);
    }

    // Cleanup ao sair
    $(window).on('beforeunload', function () {
        if (appState.refreshInterval) {
            clearInterval(appState.refreshInterval);
        }
    });
});
