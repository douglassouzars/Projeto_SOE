# Projeto Alerta de Queda

> ⚠️ **Aviso:** Todo o código-fonte e documentação técnica deste projeto estão concentrados na branch principal (`master`).

## 📌 Sobre o Projeto
Protótipo de sistema embarcado não invasivo para monitoramento e detecção de quedas em ambientes domésticos. Utilizando uma Raspberry Pi e processamento de visão computacional local (*Edge AI*), o sistema identifica quedas e, após 60 segundos de imobilidade, dispara automaticamente um alerta com registro fotográfico via Telegram para cuidadores e familiares.

## 👥 Equipe
* **Douglas Rodrigues Souza** - Configuração de SO, Scripts de Inicialização e Hardware.
* **Yuri César Carvalho Amorim** - Implementação da Visão Computacional e API do Telegram.

## 💰 Hardware Utilizado
Todo o hardware abaixo já estava disponível com a equipe, zerando os custos reais de desenvolvimento. Os valores de mercado foram listados apenas para fins de documentação:

* **Placa Principal:** Raspberry Pi 3B (R$ 420,00)
* **Módulo de Câmera:** Câmera para Raspberry Pi 5MP (R$ 45,00)
* **Alimentação:** Fonte 5V 3A 15W (R$ 35,00)
* **Armazenamento:** Cartão de Memória 32GB (R$ 60,00)
* **Acessórios:** Cabo HDMI + Case + Dissipadores + Ventoinha (R$ 51,00)

## ⚙️ Divisão de Requisitos

| ID | Nome do Requisito | Descrição | Prioridade | Responsável |
| :--- | :--- | :--- | :---: | :--- |
| **REQ-01** | Captura de Vídeo | Capturar fluxo de vídeo em tempo real a pelo menos 15 FPS. | Alta | Douglas |
| **REQ-02** | Detecção de Queda | Identificar a transição postural para deitado via visão computacional. | Alta | Yuri |
| **REQ-03** | Temporizador | Validar se o indivíduo permanece no solo por mais de 60 segundos. | Alta | Yuri |
| **REQ-04** | Alerta Telegram | Disparar mensagem de socorro via API de bot. | Alta | Douglas |
| **REQ-05** | Foto do Incidente | Anexar foto do momento da queda para avaliação visual. | Alta | Yuri |
| **REQ-06** | Daemon (Auto-boot) | Inicializar o serviço automaticamente com o sistema operacional. | Média | Douglas |
| **REQ-07** | Operação Local | Executar o processamento sem depender de nuvem (*edge computing*). | Alta | Douglas |
| **REQ-08** | Status Visual | Prover indicação em LED de que a aplicação está ativa. | Baixa | Yuri |
