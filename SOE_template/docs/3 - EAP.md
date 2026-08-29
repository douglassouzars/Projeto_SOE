# Estrutura Analítica de Produto

|**ID**|**Componente**|**Descrição**|**Dados Técnicos**|**Comentários**|
|:-:|-|-|-|-|
|1|**Sub-sistema: Hardware**|Conjunto de componentes físicos e circuitos eletrônicos do sistema embarcado.|||
|1.1|Processamento|Placa microprocessadora responsável pelo processamento local das imagens.|SoC Broadcom BCM2837, Quad-core ARM Cortex-A53 (Raspberry Pi 3B).|Central do projeto; compatível com requisitos de hardware.|
|1.2|Sensor 1|Módulo de captura de imagem para aquisição do fluxo de vídeo em tempo real.|Câmera padrão USB HD ou módulo CSI (mínimo de 15 FPS).|Fundamental para o monitoramento visual (REQ-01).|
|1.3|Sensor 2|Não aplicável.||O escopo restringe-se a uma única câmera.|
|1.4|Controle 1|Indicador visual de operação do sistema.|LED de status conectado a um pino GPIO.|Atende ao REQ-08 (Sinalização de Status Local).|
|1.5|Controle 2|Não aplicável.|||
|1.6|Comunicação 1|Módulo de rede para transmissão do alerta e pacote fotográfico.|Módulo Wi-Fi 802.11n (2.4 GHz) integrado à placa.|Essencial para a comunicação remota com a API.|
|1.7|Comunicação 2|Não aplicável.|||
|1.8|Alimentação|Fonte de energia contínua para suportar o pico computacional.|Fonte de 5V DC, capacidade de 3A, conector Micro USB.|A corrente de 3A é vital para evitar queda de tensão no SoC.|
|2|**Sub-sistema: Software**|Arquitetura lógica, algoritmos de detecção de pose e integrações externas.|||
|2.1|Controle|Lógica de estado e temporizador de permanência (validação de tempo).|Desenvolvido em Python; contagem do intervalo > 60s.|Executa o REQ-03 e gere os falsos positivos.|
|2.2|Navegação|(Adaptado para Visão Computacional) Extração de postura no quadro.|Uso de MediaPipe ou YOLO-Pose para o cálculo de eixo Y.|Identifica transição postural (REQ-02).|
|2.3|Interface|Módulo de comunicação de emergência para alertas do sistema.|Integração com Telegram Bot API via protocolo HTTP.|Entrega os dados para cuidadores e familiares (REQ-04 e 05).|
|2.4|Diagnóstico|Ferramentas de verificação de erros na execução do monitoramento.|Extração de logs nativos (journalctl) geridos pelo systemd.|Garante estabilidade e auxilia no \*debug\* do REQ-06.|
|2.5|||||
|2.6|||||
|2.7|||||
|3|**Sub-sistema: Estrutura**|Elementos físicos de acondicionamento mecânico do protótipo de bancada.|||
|3.1|Chassi|Invólucro protetor para acondicionar a placa microcomputadora.|Case compatível com o fator de forma da Raspberry Pi 3B.|Protege o circuito de danos físicos e curtos acidentais.|
|3.2|Suporte|Estrutura de fixação e direcionamento do campo de visão do sensor.|||
|3.3|Carenagem|Não aplicável|||
|3.4|Atuadores|Não aplicável||O sistema de monitoramento não possui componentes móveis.|
|3.5|Transmissão|Não aplicável|||
|3.6|Rodas/Hélices|Não aplicável||O projeto tem natureza estacionária (câmera fixa).|



