# Cronograma

**Projeto Alerta de Queda** · Início: 21/08/2026 · Término previsto: 02/12/2026 · Situação em: 02/10/2026

**Equipe:** Douglas Rodrigues Souza (sistema operacional, inicialização, _hardware_) e Yuri César Carvalho Amorim (visão computacional e API do Telegram).

Os prazos usam os dias de aula da disciplina (segunda, quarta e sexta-feira), exceto feriados (07/09, 12/10, 02/11 e 20/11). Um predecessor é a tarefa que precisa terminar para a outra poder começar.

| **ID** | **Tarefa** | **Responsável** | **Predecessor** | **Data de Início** | **Data de Conclusão** | **% de Execução** | **Status** | **Prioridade** |
|:------:|------------|-----------------|-----------------|--------------------|-----------------------|:-----------------:|-------------|----------------|
| 1 | **Planejamento** | Douglas e Yuri | – | 21/08/2026 | 02/10/2026 | 100% | Concluído | Alta |
| 1.1 | Termo de Abertura do Projeto | Douglas e Yuri | – | 21/08/2026 | 28/08/2026 | 100% | Concluído | Alta |
| 1.2 | Definição de Requisitos | Douglas e Yuri | 1.1 | 31/08/2026 | 09/09/2026 | 100% | Concluído | Alta |
| 1.3 | Definição da Estrutura Analítica do Produto | Douglas e Yuri | 1.2 | 11/09/2026 | 16/09/2026 | 100% | Concluído | Alta |
| 1.4 | Definição do Projeto Conceitual do Produto | Douglas e Yuri | 1.2, 1.3 | 18/09/2026 | 02/10/2026 | 100% | Concluído | Alta |
| 1.5 | Definição do Cronograma | Douglas e Yuri | 1.4 | 28/09/2026 | 02/10/2026 | 100% | Concluído | Média |
| 1.6 | Definição do Orçamento | Douglas | 1.1 | 31/08/2026 | 02/10/2026 | 100% | Concluído | Média |
| 2 | **Execução** | Douglas e Yuri | 1.4 | 05/10/2026 | 02/12/2026 | 0% | Não iniciado | Alta |
| 2.1 | Aquisição de Partes (LED, resistores, transistor e diodo; lente grande angular opcional) | Douglas | 1.6 | 05/10/2026 | 14/10/2026 | 0% | Não iniciado | Média |
| 2.2 | Montagem de Subsistemas | Douglas e Yuri | 1.4 | 05/10/2026 | 23/10/2026 | 0% | Não iniciado | Alta |
| 2.2.1 | Instalar e configurar o SO (Raspberry Pi OS Lite, Wi-Fi, SSH, serviços desnecessários desativados) | Douglas | 1.4 | 05/10/2026 | 14/10/2026 | 0% | Não iniciado | Alta |
| 2.2.2 | Montar a câmera CSI-2 e o suporte | Douglas | 2.2.1 | 14/10/2026 | 16/10/2026 | 0% | Não iniciado | Alta |
| 2.2.3 | Montar o circuito da ventoinha (PWM) e do LED | Douglas | 2.1 | 16/10/2026 | 23/10/2026 | 0% | Não iniciado | Média |
| 2.2.4 | Preparar o ambiente Python e o modelo de pose | Yuri | 2.2.1 | 14/10/2026 | 23/10/2026 | 0% | Não iniciado | Alta |
| 2.2.5 | Criar o bot do Telegram (token e chat de destino) | Yuri | 1.4 | 07/10/2026 | 14/10/2026 | 0% | Não iniciado | Alta |
| 2.3 | Testes de Subsistemas | Douglas e Yuri | 2.2.2, 2.2.5 | 19/10/2026 | 04/11/2026 | 0% | Não iniciado | Alta |
| 2.3.1 | Testar a captura de vídeo a 15 FPS (REQ-01) | Douglas | 2.2.2 | 19/10/2026 | 21/10/2026 | 0% | Não iniciado | Alta |
| 2.3.2 | Testar a ventoinha, o LED, a temperatura e a tensão de alimentação sob carga (REQ-08) | Douglas | 2.2.3 | 26/10/2026 | 28/10/2026 | 0% | Não iniciado | Média |
| 2.3.3 | Testar a detecção de pose em vídeos gravados e calibrar os limiares (REQ-02) | Yuri | 2.2.4 | 26/10/2026 | 04/11/2026 | 0% | Não iniciado | Alta |
| 2.3.4 | Testar o envio de mensagem com foto pelo Telegram (REQ-04 e REQ-05) | Yuri | 2.2.5 | 19/10/2026 | 21/10/2026 | 0% | Não iniciado | Alta |
| 2.3.5 | Testar a inicialização automática e o _watchdog_ (REQ-06) | Douglas | 2.2.1 | 30/10/2026 | 04/11/2026 | 0% | Não iniciado | Média |
| 2.4 | Integração de Subsistemas | Douglas e Yuri | 2.3.3, 2.3.4 | 06/11/2026 | 16/11/2026 | 0% | Não iniciado | Alta |
| 2.4.1 | Integrar as _threads_, a máquina de estados e o temporizador (REQ-02, REQ-03 e REQ-07) | Yuri | 2.3.3, 2.3.4 | 06/11/2026 | 11/11/2026 | 0% | Não iniciado | Alta |
| 2.4.2 | Integrar o serviço `systemd` (inicialização automática e _token_ em arquivo de ambiente) | Douglas | 2.4.1, 2.3.5 | 11/11/2026 | 16/11/2026 | 0% | Não iniciado | Alta |
| 2.4.3 | Otimizar o desempenho (meta de 15 FPS na Raspberry Pi 3B) | Douglas e Yuri | 2.4.1 | 11/11/2026 | 16/11/2026 | 0% | Não iniciado | Alta |
| 2.5 | Testes de Integração | Douglas e Yuri | 2.4.2, 2.4.3 | 18/11/2026 | 27/11/2026 | 0% | Não iniciado | Alta |
| 2.5.1 | Testar o fluxo completo: queda simulada, permanência de 60 s e alerta no Telegram | Douglas e Yuri | 2.4.2, 2.4.3 | 18/11/2026 | 23/11/2026 | 0% | Não iniciado | Alta |
| 2.5.2 | Testar iluminação, latência e falsos positivos (agachar, sentar, deitar) | Douglas e Yuri | 2.5.1 | 23/11/2026 | 27/11/2026 | 0% | Não iniciado | Alta |
| 2.5.3 | Testar a robustez (queda de energia e perda de Wi-Fi) | Douglas | 2.5.1 | 23/11/2026 | 25/11/2026 | 0% | Não iniciado | Média |
| 2.6 | Apresentação Final | Douglas e Yuri | 2.5.1 | 25/11/2026 | 02/12/2026 | 0% | Não iniciado | Alta |
| 3 | **Documentação** | Douglas e Yuri | – | 21/08/2026 | 02/12/2026 | 67% | Em andamento | Alta |
| 3.1 | Termo de Abertura do Projeto | Douglas e Yuri | 1.1 | 21/08/2026 | 28/08/2026 | 100% | Concluído | Alta |
| 3.2 | Requisitos | Douglas e Yuri | 1.2 | 31/08/2026 | 09/09/2026 | 100% | Concluído | Alta |
| 3.3 | Estrutura Analítica do Produto | Douglas e Yuri | 1.3 | 11/09/2026 | 16/09/2026 | 100% | Concluído | Alta |
| 3.4 | Projeto Conceitual do Produto | Douglas e Yuri | 1.4 | 18/09/2026 | 02/10/2026 | 100% | Concluído | Alta |
| 3.5 | Cronograma | Douglas e Yuri | 1.5 | 28/09/2026 | 02/10/2026 | 100% | Concluído | Média |
| 3.6 | Orçamento | Douglas | 1.6 | 31/08/2026 | 02/10/2026 | 100% | Concluído | Média |
| 3.7 | Testes | Douglas e Yuri | 2.3.1 | 26/10/2026 | 27/11/2026 | 0% | Não iniciado | Média |
| 3.8 | Avaliação de Desempenho | Douglas e Yuri | 2.5.2 | 27/11/2026 | 30/11/2026 | 0% | Não iniciado | Alta |
| 3.9 | Documento Final | Douglas e Yuri | 3.8 | 30/11/2026 | 02/12/2026 | 0% | Não iniciado | Alta |

## Marcos do projeto

| **Data** | **Marco** |
|:--------:|-----------|
| 21/08/2026 | Início do projeto |
| 02/10/2026 | Projeto conceitual (hardware e software) e cronograma concluídos |
| 23/10/2026 | Subsistemas montados |
| 04/11/2026 | Subsistemas testados e limiares de detecção calibrados |
| 16/11/2026 | Sistema integrado e otimizado |
| 27/11/2026 | Testes de integração concluídos |
| 02/12/2026 | Apresentação final e entrega do documento final |

## Observações

- **Carga de trabalho:** restam 23 aulas até o término (≈ 23 h por integrante), a serem complementadas com trabalho extraclasse nas semanas de integração (06/11 a 16/11) e de testes (18/11 a 27/11).
- **Risco principal: desempenho.** Manter 15 FPS com estimativa de pose na Raspberry Pi 3B é o ponto mais crítico. A tarefa 2.4.3 e a folga de 27/11 a 02/12 existem para tratá-lo; o plano alternativo é reduzir a resolução, processar um quadro a cada dois ou usar um modelo mais leve.
- **Risco: rede.** O alerta depende de Wi-Fi e da API do Telegram. A lógica de novas tentativas é testada na tarefa 2.5.3.
- **Risco: aquisição de partes.** Os itens principais já estão disponíveis; só componentes avulsos de baixo custo precisam ser comprados (tarefa 2.1). A lente grande angular é opcional.
- **Atualização:** a coluna "% de Execução" e o status serão atualizados a cada entrega no repositório.
