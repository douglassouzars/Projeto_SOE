# Requisitos

|**ID**|**Nome do Requisito**|**Descrição**|**Prioridade**|**Responsável**|**Observações**|
|:-:|-|-|:-:|-|-|
|1|Captura de Vídeo Contínua|O sistema deve capturar fluxo de vídeo em tempo real no ambiente monitorado a pelo menos 15 FPS.|Alta|Douglas|Utilização de câmera CSI ou webcam USB conectada à Raspberry Pi.|
|2|Detecção de Queda|O software deve identificar a transição postural de em pé/sentado para deitado no chão via visão computacional.|Alta|Yuri|Baseado em proporção de bounding box ou keypoints de pose corporal.|
|3|Temporizador de Permanência|O sistema deve iniciar um contador de tempo ao detectar a queda e validar se o indivíduo permanece no solo por mais de 60 segundos.|Alta|Yuri|Evita falsos positivos em agachamentos ou deitadas voluntárias temporárias.|
|4|Envio de Alerta via Telegram|Ao expirar o tempo limite de 60 s, o sistema deve disparar uma mensagem de socorro via API de bot para o chat/grupo configurado.|Alta|Douglas|Requer conexão com a internet ativa via Wi-Fi.|
|5|Envio de Registro Fotográfico|O alerta deve conter em anexo a foto do momento da queda para avaliação visual rápida pelo cuidador.|Alta|Yuri|A imagem deve ser comprimida/salva temporariamente antes do upload.|
|6|Inicialização Automática (Daemon)|O serviço de monitoramento deve inicializar automaticamente junto com o boot do sistema operacional da Raspberry Pi.|Média|Douglas|Implementação via serviço systemd para garantir resiliência após quedas de energia.|
|7|Operação Autônoma e Local|Todo o processamento de visão e lógica de tempo deve ser executado localmente (edge computing), sem depender de streaming contínuo em nuvem.|Alta|Douglas|Preserva a privacidade do usuário no ambiente doméstico.|
|8|Sinalização de Status Local|O sistema deve prover indicação visual básica de que a aplicação está em execução ativa no ambiente.|Baixa|Yuri|Uso de LEDs de status da placa ou indicador luminoso auxiliar.|
|9||||||
|10||||||
|11||||||
|12||||||
|13||||||
|14||||||
|15||||||
|16||||||



