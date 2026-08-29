# Termo de Abertura do Projeto

* **Nome do Projeto: Projeto Alerta de Queda**
* **Data de Início: 21/08/2026**
* **Data de Término: Estimativa em 02/12/2026**

## Visão Geral do Projeto

### Descrição do Problema

As quedas em ambientes domésticos representam um risco severo para idosos e pessoas com distúrbios de equilíbrio (como labirintite e vertigem), podendo resultar em perda de consciência, lesões graves e imobilidade prolongada no solo sem o devido socorro. O público afetado apresenta, frequentemente, dificuldades de adaptação a tecnologias de monitoramento, resultando em subnotificação de acidentes e atraso no atendimento de emergência, o que pode agravar o quadro clínico pós-queda.

### Estado da arte

As soluções atuais para detecção de quedas dividem-se principalmente em dispositivos vestíveis (wearables, como smartwatches equipados com acelerômetros e giroscópios) e sistemas baseados em visão computacional e sensores ambientais (câmeras RGB, sensores infravermelhos e radares de ondas milimétricas).



Embora os wearables sejam comuns, eles enfrentam limitações severas de adesão em idosos e pessoas com crises de labirintite, devido ao esquecimento de uso, desconforto contínuo e à necessidade constante de recarga da bateria \[1]. Os sistemas baseados em visão computacional processada em borda (Edge AI), utilizando modelos leves de estimativa de pose (como MediaPipe ou YOLO-Pose) \[2], representam a abordagem mais moderna. Eles não são invasivos, dispensam a cooperação ativa do usuário e permitem a validação contextual da postura corporal antes do envio do alerta.

### Objetivos

Desenvolver um protótipo de sistema embarcado não invasivo de monitoramento e detecção de quedas em ambientes domésticos utilizando Raspberry Pi e visão computacional, com envio automático de alertas e registro visual via Telegram em caso de imobilidade prolongada no solo.



Objetivos Específicos:

* Implementar e otimizar um algoritmo de detecção de postura/queda em tempo real executando diretamente na Raspberry Pi.
* Desenvolver a lógica de temporização que avalia a permanência da pessoa no chão por um intervalo crítico superior a 1 minuto (evitando falsos positivos).
* Integrar a captura de frames da câmera com a API de bots do Telegram para transmissão do alerta e envio da foto aos contatos de emergência.
* Validar a acurácia, latência e robustez do sistema sob diferentes condições de iluminação em ambiente de teste controlado.



### Escopo do Projeto

O que faz parte do escopo:



* Aquisição de vídeo em tempo real via câmera conectada à Raspberry Pi.
* Processamento de imagens local (edge processing) para identificação do estado de queda.
* Contador em software para verificação da permanência no solo (> 60 segundos).
* Módulo de comunicação de rede para envio de mensagem de socorro com anexo fotográfico via Telegram Bot.
* Configuração do sistema operacional embarcado e scripts de inicialização automática do serviço na placa.



O que NÃO faz parte do escopo:



* Monitoramento de múltiplos cômodos simultâneos.
* Reconhecimento facial ou identificação biométrica do indivíduo.
* Integração direta com centrais públicas de emergência (SAMU, Bombeiros, 190).
* Design ou injeção de case plástico industrial final (o protótipo utilizará montagem de bancada).
* Operação em escuridão total (a menos que seja utilizada câmera IR dedicada).

### *Stakeholders*

* Usuários Finais Primários: Idosos, portadores de labirintite, enxaqueca vestibular ou distúrbios de equilíbrio suscetíveis a quedas.
* Usuários Finais Secundários (Cuidadores e Familiares): Pessoas que receberão os alertas no Telegram e necessitam de rapidez para acionar socorro.
* Equipe de Desenvolvimento: Alunos responsáveis pela concepção, implementação, integração do hardware e testes de validação.
* Corpo Docente: Professores e avaliadores responsáveis por orientar e acompanhar a execução técnica da disciplina.

## Recursos do Projeto

### Membros da Equipe

|**Nome**|**Matrícula**|**Curso**|**Funções**|
|-|-|-|-|
|Douglas Rodrigues Souza|170120520|Engenharia Eletrônica|Configuração de SO, Scripts de Inicialização e Hardware|
|Yuri César Carvalho Amorim|150152671|Engenharia Eletrônica|Implementação da Visão Computacional e API do Telegram|

### Orçamento estimado (R$)

O orçamento foi estimado considerando o aproveitamento de hardware já disponível, minimizando os custos para a equipe:

* Placa Principal: Raspberry Pi 3B (recurso já disponível)- Valor de Mercado R$ 420,00
* Módulo: Câmera para Raspberry Pi 5MP (recurso já disponível)- Valor de Mercado R$ 45,00
* Alimentação: Fonte 5V 3A 15W (recurso já disponível)- Valor de Mercado R$ 35,00
* Armazenamento: Cartão de Memoria 32gb (recurso já disponível)- Valor de Mercado R$ 60,00
* Acessórios: Cabo HDMI + Case + Dissipadores + Ventoinha(recurso já disponível)- Valor de Mercado R$ 51,00



### Esforço estimado (horas)

Estima-se que o projeto demandará um esforço total de 80 horas, sendo aproximadamente 40 horas de dedicação por membro da equipe, divididas ao longo do semestre letivo entre pesquisa bibliográfica, configuração do ambiente embarcado, implementação do código, testes e escrita da documentação. Tal base de cálculo decorre da data de início do projeto até a data estimada de término, considerando todos os dias de aula da disciplina (segunda, quarta e sexta-feira), nos quais cada membro disponibilizará 1 hora para aplicar no projeto os conhecimentos adquiridos.

## Referências

1. M. L. Chung et al., "Uso de visão computacional para detecção de quedas em tempo real," 2025.
2. I. A. Cabral et al., "Protótipo de computação vestível para monitoramento de locomoção de idoso utilizando Node-RED com ESP32 e Raspberry PI," 2022.
3. Dev Ideias, "Detecção de Quedas com Visão Computacional | Tutorial," YouTube, 21 dez. 2023. \[Online]. Disponível em: https://youtu.be/Afjaa9Xv6pU?si=OyNfNANkUEKbf77G

