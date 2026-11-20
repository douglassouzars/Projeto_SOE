#!/usr/bin/env python3
"""
silhueta.py — Detector de quedas por SILHUETA, para câmera no TETO (vista zenital).
Projeto Alerta de Queda (SOE). Protótipo para calibração AO VIVO no notebook.

Ideia: vista de cima, uma pessoa EM PÉ aparece como uma mancha pequena e quase
redonda (cabeça + ombros); DEITADA, como uma mancha grande e alongada (corpo
inteiro no chão). Queda = passar de "em pé" para "deitado" RAPIDAMENTE.

Etapas por quadro:
  1. subtração de fundo (MOG2): separa o que é diferente do chão vazio;
  2. maior mancha -> área e alongamento (lado maior / lado menor do retângulo);
  3. máquina de estados: IDLE -> MONITORANDO -> CRITICO -> ALERTA;
     gravidade: levantou em < 60 s = LEVE; ficou no chão = GRAVE.

Uso no NOTEBOOK (abre janelas):
  pip install opencv-python numpy
  python silhueta.py                 # webcam 0
  python silhueta.py --camera 1      # webcam USB externa
  python silhueta.py --teste         # tempo crítico de 5 s (p/ testar rápido)
  Teclas na janela: b = reaprende o fundo, q = sai

Uso na RASPBERRY PI (sem tela: a imagem vai para o navegador do notebook):
  python3 silhueta.py --teste --web 8080
  No notebook, abra  http://yuri-pi.local:8080
  (botão na página = reaprende o fundo; Ctrl+C no terminal = sai)

IMPORTANTE: ao iniciar, deixe a área filmada VAZIA por 3 s (o programa
aprende como é o chão sem ninguém). Depois entre em cena.
"""

import argparse
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from dataclasses import dataclass, field
from enum import Enum

import cv2
import numpy as np

# ------------------------ Parâmetros (calibrar ao vivo) ------------------------
LARG, ALT = 320, 240             # resolução de processamento (leve p/ a Pi 3B)
AQUECIMENTO_S = 3.0              # espera foco/exposição da câmera estabilizarem
APRENDER_FUNDO_S = 3.0           # depois, aprende o fundo por 3 s
AREA_MAX = 0.60                  # mancha > 60% do quadro não é pessoa: fundo mudou
                                 # (câmera baixa: pessoa em pé chega a ~40-50%)
FUNDO_MUDOU_S = 8.0              # fundo errado E imagem PARADA por 8 s -> reaprende
IMAGEM_PARADA = 0.01             # < 1% dos pixels mudando = ninguém se mexendo
                                 # (se há alguém se mexendo, NÃO reaprende: senão
                                 #  a pessoa vira parte do fundo)
JANELA_REF_S = 30.0              # referência "em pé" = áreas compactas dos últimos 30 s
PERCENTIL_REF = 20               # usa as MENORES (em pé < sentado < agachado)
TAXA_APRENDIZADO = 0.0005        # em IDLE: fundo se adapta devagar (luz, objetos)
AREA_MIN = 0.004                 # mancha < 0,4% do quadro = ruído, ignora (calibrar no teto)
VAR_MIN_FUNDO = 60               # variância mínima do fundo (desvio ~8 níveis)
                                 # (teste2: manchas de ruído com 0,5-1,9%; pessoa
                                 #  deitada no canto oposto ~8%)
QUADRO_CORROMPIDO = 0.5          # >50% dos pixels mudando de um quadro p/ outro
                                 # = quadro corrompido pelo USB: é descartado

ALONG_EM_PE = 2.0                # alongamento <= 2,0 -> "em pé" (mancha redonda)
ALONG_DEITADO = 2.6              # alongamento >= 2,6 -> "deitado" (histerese)
ALONG_DEITADO_CORTADO = 1.7      # idem p/ corpo cortado pela borda (só queda lenta)
AREA_CORTADO_MIN = 0.15          # ...e só se a mancha for grande (pessoa, não ruído)
ALONG_RECUPERA = 2.3             # levantou = 3 s seguidos com alongamento <= 2,3
RAZAO_AREA_DEITADO = 0.5         # deitado ocupa >= metade da área em pé
# Calibração (teste real, 17/11): deitado = alongamento 3,3–3,7 mas ÁREA
# PARECIDA com a de pé (1,0–1,3x). Motivo: perspectiva. Em pé, cabeça e
# ombros ficam bem mais PERTO da lente e aparecem ampliados; deitado, o corpo
# está no chão, mais longe. Por isso a área NÃO distingue as posturas e o
# critério principal é o ALONGAMENTO. A área só descarta manchas pequenas
# alongadas (um braço entrando na imagem).

JANELA_QUEDA_S = 1.5             # em pé -> deitado em até 1,5 s = QUEDA
                                 # (deitar-se devagar leva mais tempo)
CONFIRMA_S = 0.5                 # precisa PERMANECER deitado 0,5 s p/ confirmar
QUEDA_LENTA_S = 20.0            # deitado no chão por 20 s seguidos = queda LENTA
                                # (tontura: a pessoa cede aos poucos; não depende
                                #  da velocidade). Câmera NÃO pode ver cama/sofá.
TOLERANCIA_CHAO_S = 2.0         # oscilação curta da forma não zera a contagem
JANELA_LENTA_S = 30.0           # em pé no máximo 30 s antes de ir ao chão
FRACAO_CHAO = 0.7                # queda lenta: >=70% dos quadros com forma deitada
EM_PE_MIN_S = 1.0               # forma compacta por >= 1 s = estava em pé
TEMPO_CRITICO_S = 60.0           # 60 s no chão -> queda GRAVE
TEMPO_RECUPERACAO_S = 3.0        # em pé por 3 s seguidos -> levantou
COOLDOWN_ALERTA_S = 300.0        # intervalo mínimo entre alertas graves
TOLERANCIA_SUMICO_S = 5.0        # mancha some por mais que isso -> zera
LIMIAR_IMOVEL = 0.02             # < 2% da mancha mudando por quadro = imóvel


class Estado(Enum):
    IDLE = "IDLE"
    MONITORANDO = "MONITORANDO"
    CRITICO = "CRITICO"
    ALERTA = "ALERTA"


@dataclass
class Medida:
    detectado: bool = False
    fundo_mudou: bool = False    # mancha grande demais p/ ser pessoa
    borda: bool = False          # mancha encosta na borda (pessoa só em parte)
    cortada: bool = False        # borda corta a mancha numa faixa larga
    mov_global: float = 1.0      # fração da imagem INTEIRA que mudou
    descartado: bool = False     # quadro corrompido, ignorado
    area: float = 0.0            # fração do quadro ocupada pela mancha
    along: float = 0.0           # lado maior / lado menor
    movimento: float = 0.0       # fração da mancha que mudou desde o quadro anterior
    contorno: np.ndarray = None
    retangulo: tuple = None


# ------------------------------- Percepção -------------------------------
class Silhueta:
    """Subtração de fundo + análise da maior mancha."""

    def __init__(self, compensar=True):
        self.compensar = compensar      # False com --exposicao (câmera fixa)
        self.total_descartados = 0      # contadores do teste inteiro
        self.total_quadros = 0
        self.reinicia()
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    def reinicia(self):
        self.fundo = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=32, detectShadows=True)
        # Variância mínima do fundo: aprendido com a cena totalmente parada, o
        # modelo fica com variância quase zero e QUALQUER variação global de
        # brilho (luz do dia mudando, ajuste da câmera) marca o chão inteiro
        # como pessoa (cam_brio4: o chão escureceu ~6% e a máscara ficou
        # toda branca). Com este piso, pequenas variações são toleradas.
        self.fundo.setVarMin(VAR_MIN_FUNDO)
        self.cinza_ant = None
        self.mascara_ant = None
        self.ganho = 1.0
        self.descartados = 0

    def compensa_brilho(self, peq, taxa):
        """Compensação de exposição POR SOFTWARE.
        A webcam reajusta o brilho da imagem inteira quando alguém entra em
        cena. Aqui o quadro é reescalado para que o FUNDO (pixels fora da
        última máscara) tenha o mesmo brilho do fundo aprendido. Assim a
        variação global não vira 'pessoa' na máscara, sem mexer na câmera."""
        if taxa == -1 or self.mascara_ant is None or not self.compensar:
            return peq          # aprendendo, ou exposição manual (desnecessária)
        fundo_img = self.fundo.getBackgroundImage()
        if fundo_img is None:
            return peq
        livre = self.mascara_ant == 0
        if np.count_nonzero(livre) < 0.2 * livre.size:
            # máscara anterior quase toda branca (justamente o efeito de uma
            # mudança de exposição): usa a imagem inteira p/ sair do impasse
            livre = np.ones_like(livre, dtype=bool)
        g_q = cv2.cvtColor(peq, cv2.COLOR_BGR2GRAY)[livre]
        g_f = cv2.cvtColor(fundo_img, cv2.COLOR_BGR2GRAY)[livre]
        med_q = float(np.median(g_q))
        if med_q < 5:
            return peq
        alvo = float(np.clip(np.median(g_f) / med_q, 0.4, 2.5))
        self.ganho = 0.5 * self.ganho + 0.5 * alvo          # suaviza
        return cv2.convertScaleAbs(peq, alpha=self.ganho)

    def processa(self, quadro, taxa):
        peq = cv2.resize(quadro, (LARG, ALT))
        peq = self.compensa_brilho(peq, taxa)
        cinza = cv2.GaussianBlur(cv2.cvtColor(peq, cv2.COLOR_BGR2GRAY), (5, 5), 0)

        # Quadro corrompido pelo USB (faixas deslocadas, visto em teste2 aos
        # 3-4 s): mais da metade da imagem muda num único quadro. Descarta,
        # para não contaminar o fundo nem a máquina de estados. Após 5
        # descartes seguidos aceita (mudança real e persistente da cena).
        self.total_quadros += 1
        if self.cinza_ant is not None and self.descartados < 5:
            dif = np.count_nonzero(cv2.absdiff(cinza, self.cinza_ant) > 40) / cinza.size
            if dif > QUADRO_CORROMPIDO:
                self.descartados += 1
                self.total_descartados += 1
                vazia = np.zeros((ALT, LARG), np.uint8)
                m = Medida()
                m.descartado = True
                return peq, vazia, m
        self.descartados = 0

        mascara = self.fundo.apply(peq, learningRate=taxa)
        # MOG2 marca sombra com 127 e objeto com 255: fica só o objeto
        _, mascara = cv2.threshold(mascara, 200, 255, cv2.THRESH_BINARY)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, self.kernel)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, self.kernel, iterations=2)
        self.mascara_ant = mascara

        m = Medida()
        if self.cinza_ant is not None:
            m.mov_global = np.count_nonzero(cv2.absdiff(cinza, self.cinza_ant) > 20) / cinza.size
        contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)
        if contornos:
            c = max(contornos, key=cv2.contourArea)
            area = cv2.contourArea(c) / (LARG * ALT)
            if area > AREA_MAX:
                m.fundo_mudou = True     # luz mudou / câmera mexeu / fundo errado
            elif area >= AREA_MIN:
                ret = cv2.minAreaRect(c)
                (_, _), (w, h), _ = ret
                m.detectado = True
                m.area = area
                m.along = max(w, h) / max(1.0, min(w, h))
                m.contorno = c
                m.retangulo = ret
                x, y, w2, h2 = cv2.boundingRect(c)
                m.borda = x <= 1 or y <= 1 or x + w2 >= LARG - 1 or y + h2 >= ALT - 1
                if m.borda:
                    # quanto da mancha está colada na moldura da imagem?
                    so = np.zeros_like(mascara)
                    cv2.drawContours(so, [c], -1, 255, cv2.FILLED)
                    contato = max(np.count_nonzero(so[0]), np.count_nonzero(so[-1]),
                                  np.count_nonzero(so[:, 0]), np.count_nonzero(so[:, -1]))
                    m.cortada = contato > 0.6 * min(w, h)
                # movimento DENTRO da mancha (p/ saber se a pessoa está imóvel)
                if self.cinza_ant is not None:
                    so_mancha = np.zeros_like(mascara)
                    cv2.drawContours(so_mancha, [c], -1, 255, cv2.FILLED)
                    dif = cv2.absdiff(cinza, self.cinza_ant) > 20
                    pix = cv2.countNonZero(so_mancha)
                    m.movimento = np.count_nonzero(dif & (so_mancha > 0)) / max(1, pix)

        self.cinza_ant = cinza
        return peq, mascara, m


# --------------------------- Máquina de estados ---------------------------
class FSM:
    def __init__(self, on_evento):
        self.on_evento = on_evento
        self.estado = Estado.IDLE
        self.area_ref = None      # área típica da pessoa EM PÉ (aprendida)
        self.compactas = []       # (t, área) de manchas compactas recentes
        self.t_em_pe = None       # último instante em pé (sustentado)
        self.t_compacto_ini = None  # início da sequência contínua compacta
        self.t_chao_ini = None    # início da permanência deitado no chão
        self.n_chao = self.n_total = 0   # quadros no chão / total desde t_chao_ini
        self.t_ultimo_deitado = None
        self.tipo_queda = None
        self.t_deitado_ini = None # início da sequência contínua "deitado"
        self.t_erguido = None     # início da sequência contínua "em pé"
        self.t_queda = None
        self.t_ultima_det = None
        self.t_ultimo_alerta = -1e9
        self.transicao_s = 0.0
        self.movs = []

    def classifica(self, m):
        # EM PÉ depende só da FORMA (mancha compacta). Vale mesmo encostando
        # na borda: com a câmera baixa, a pessoa em pé quase sempre encosta
        # nela, e a queda precisa saber que ela estava em pé. (A REFERÊNCIA de
        # tamanho, abaixo, só é aprendida com a pessoa inteira na imagem.)
        em_pe = m.along <= ALONG_EM_PE
        # DEITADO: mancha alongada E bem maior que a pessoa em pé.
        ref = self.area_ref
        deitado = m.along >= ALONG_DEITADO and (ref is None or m.area >= RAZAO_AREA_DEITADO * ref)
        return em_pe, deitado

    def passo(self, m, t):
        antes = self.estado

        if not m.detectado:
            if (self.estado != Estado.IDLE and self.t_ultima_det is not None
                    and t - self.t_ultima_det > TOLERANCIA_SUMICO_S):
                self._zera()
            self._log(antes, m)
            return self.estado

        self.t_ultima_det = t
        em_pe, deitado = self.classifica(m)

        # "Em pé" para fins de queda exige a forma compacta SUSTENTADA por
        # EM_PE_MIN_S. Rolar no chão passa por formas compactas por instantes
        # (cam_brio3, 32 s) e não pode contar como "estava em pé".
        self.t_compacto_ini = (self.t_compacto_ini or t) if em_pe else None
        if em_pe and t - self.t_compacto_ini >= EM_PE_MIN_S:
            self.t_em_pe = t
        if em_pe:
            if self.estado == Estado.IDLE and not m.borda:
                # Referência "em pé" (só com a pessoa INTEIRA: um pedaço do
                # corpo na borda, como uma mão, não serve): vista de cima, em pé, sentado e agachado
                # são todos manchas compactas, mas EM PÉ é a MENOR delas.
                # Por isso usa um percentil baixo das áreas compactas dos
                # últimos 30 s (agachar não "contamina" a referência).
                self.compactas.append((t, m.area))
                self.compactas = [(ti, a) for ti, a in self.compactas
                                  if t - ti <= JANELA_REF_S]
                self.area_ref = float(np.percentile(
                    [a for _, a in self.compactas], PERCENTIL_REF))
        # Recuperação = 3 s seguidos SEM estar deitado. Antes exigia 3 s
        # seguidos "em pé" (alongamento <= 2,0), mas o alongamento oscila
        # entre 1,7 e 2,2 de um quadro para outro e zerava a contagem: o
        # sistema ficava preso em ALERTA (bug visto no teste de 17/11).
        # Ajuste (teste cam_brio3, 19/11): deitado de bruços o alongamento caiu
        # para 2,4-2,5 (entre os dois limites), contou como "não deitado" e o
        # alarme foi encerrado com a pessoa ainda no chão. Agora a contagem
        # só corre com alongamento <= ALONG_RECUPERA (em pé mede 1,1-2,2).
        # Corpo deitado CORTADO pela borda (pernas fora da imagem) tem o
        # alongamento subestimado (cam_brio6: 1,9 em vez de >2,6). Conta
        # como "no chão" se for grande (pessoa perto da lente, não ruído
        # nem gato) e alongado acima de ALONG_DEITADO_CORTADO.
        cortado_no_chao = (m.cortada and m.along >= ALONG_DEITADO_CORTADO
                           and m.area >= AREA_CORTADO_MIN)
        if m.along <= ALONG_RECUPERA and not cortado_no_chao:
            self.t_erguido = self.t_erguido or t
        else:
            self.t_erguido = None

        # Para INICIAR uma queda, a mancha deitada não pode estar CORTADA pela
        # borda (encostar com um pé tudo bem): cortada, a forma não é confiável (teste3, 37 s: pessoa
        # em pé bem perto da lente, cortada pela borda, pareceu alongada e
        # gerou alarme falso). Durante o monitoramento a borda não importa.
        self.t_deitado_ini = ((self.t_deitado_ini or t)
                              if deitado and not m.cortada else None)
        # Permanência no chão (queda lenta): tolera oscilações curtas.
        no_chao = (deitado and not m.cortada) or cortado_no_chao
        if no_chao:
            if self.t_chao_ini is None:
                self.t_chao_ini = t
                self.n_chao = self.n_total = 0
            self.t_ultimo_deitado = t
        elif (self.t_ultimo_deitado is None
              or t - self.t_ultimo_deitado > TOLERANCIA_CHAO_S):
            self.t_chao_ini = None
        # Ficou EM PÉ (forma compacta sustentada) depois de "deitar": não é
        # permanência no chão. Sem isso, manchas cortadas e ruidosas de quem
        # anda perto da lente mantinham a contagem viva (teste2, 42-51 s).
        if self.t_em_pe == t and not no_chao:
            self.t_chao_ini = None
        if self.t_chao_ini is not None:   # fração dos quadros realmente "no chão"
            self.n_total += 1
            self.n_chao += no_chao
        levantou = self.t_erguido is not None and t - self.t_erguido >= TEMPO_RECUPERACAO_S

        if self.estado == Estado.IDLE:
            confirmado = (self.t_deitado_ini is not None
                          and t - self.t_deitado_ini >= CONFIRMA_S)
            if confirmado and self.t_em_pe is not None:
                self.transicao_s = self.t_deitado_ini - self.t_em_pe
                if self.transicao_s <= JANELA_QUEDA_S:     # rápido = queda
                    self.estado = Estado.MONITORANDO
                    self.t_queda = t
                    self.tipo_queda = "rapida"
                    self.movs = []
            # Queda LENTA: deitado no chão tempo demais, qualquer que tenha
            # sido a descida. O tempo no chão conta desde que deitou.
            # Exige uma PESSOA vista em pé pouco antes de ir ao chão (evita que
            # ruído ou objetos numa cena vazia virem "queda lenta").
            pessoa_antes = (self.t_em_pe is not None and
                            self.t_chao_ini is not None and
                            self.t_chao_ini - self.t_em_pe <= JANELA_LENTA_S)
            # E exige a forma deitada na MAIORIA dos quadros (não só picos
            # isolados de uma mancha ruidosa de quem está em pé).
            if (self.estado == Estado.IDLE and pessoa_antes
                    and t - self.t_chao_ini >= QUEDA_LENTA_S
                    and self.n_chao >= FRACAO_CHAO * self.n_total):
                self.estado = Estado.MONITORANDO
                self.t_queda = self.t_chao_ini
                self.tipo_queda = "lenta"
                self.transicao_s = 0.0
                self.movs = []

        elif self.estado == Estado.MONITORANDO:
            self.movs.append(m.movimento)
            if levantou:
                info = self._info(t)
                self._zera()
                self.on_evento("queda_leve", info)
            elif t - self.t_queda >= TEMPO_CRITICO_S:
                self.estado = Estado.CRITICO

        if self.estado == Estado.CRITICO:
            if levantou:
                self._zera()
            elif t - self.t_ultimo_alerta >= COOLDOWN_ALERTA_S:
                self.t_ultimo_alerta = t
                self.on_evento("queda_grave", self._info(t))
                self.estado = Estado.ALERTA

        elif self.estado == Estado.ALERTA and levantou:
            self._zera()

        self._log(antes, m)
        return self.estado

    def _info(self, t):
        mov = float(np.mean(self.movs)) if self.movs else 0.0
        return {"tipo": self.tipo_queda or "-",
                "transicao_s": round(self.transicao_s, 2),
                "tempo_no_chao_s": round(t - self.t_queda, 1),
                "imovel": mov < LIMIAR_IMOVEL,
                "movimento": round(mov, 3)}

    def _zera(self):
        self.estado = Estado.IDLE
        self.t_chao_ini = None
        self.tipo_queda = None
        self.t_queda = None
        self.t_erguido = None
        self.movs = []

    def _log(self, antes, m):
        if self.estado != antes:
            print(f"[FSM] {antes.value} -> {self.estado.value} "
                  f"(along={m.along:.1f} area={m.area:.3f})")


# ---------------------- Visualização pela rede (modo --web) ----------------------
class Transmissor:
    """Servidor HTTP mínimo: entrega o quadro mais recente como vídeo MJPEG,
    que qualquer navegador exibe. Roda em thread própria."""

    PAGINA = b"""<!doctype html><html><head><meta charset="utf-8">
<title>Silhueta - Pi</title></head>
<body style="background:#111;color:#eee;font-family:sans-serif;text-align:center">
<h3>Detector de quedas - camera da Raspberry Pi</h3>
<img src="/stream" style="max-width:100%"><br><br>
<a href="/fundo"><button style="font-size:18px;padding:8px 20px">
Reaprender fundo (deixe a cena vazia)</button></a>
<p>Esquerda: camera com a deteccao. Direita: mascara (branco = pessoa).</p>
</body></html>"""

    def __init__(self, porta):
        self.jpeg = None
        self.trava = threading.Condition()
        self.pedir_fundo = False
        transmissor = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):          # silencia o log de cada acesso
                pass

            def do_GET(self):
                if self.path == "/fundo":
                    transmissor.pedir_fundo = True
                    self.send_response(303)
                    self.send_header("Location", "/")
                    self.end_headers()
                elif self.path == "/stream":
                    self.send_response(200)
                    self.send_header("Content-Type",
                                     "multipart/x-mixed-replace; boundary=quadro")
                    self.end_headers()
                    try:
                        while True:
                            with transmissor.trava:
                                transmissor.trava.wait(timeout=2)
                                dados = transmissor.jpeg
                            if dados is None:
                                continue
                            self.wfile.write(b"--quadro\r\nContent-Type: image/jpeg\r\n"
                                             + f"Content-Length: {len(dados)}\r\n\r\n".encode()
                                             + dados + b"\r\n")
                    except (BrokenPipeError, ConnectionResetError):
                        pass                     # navegador fechou a página
                else:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(Transmissor.PAGINA)

        # Escuta em IPv6 E IPv4 ("::" no Linux aceita os dois): no Windows,
        # "yuri-pi.local" costuma resolver para o endereço IPv6 da Pi.
        class ServidorDuplo(ThreadingHTTPServer):
            address_family = socket.AF_INET6

        try:
            self.servidor = ServidorDuplo(("::", porta), Handler)
        except OSError:                  # sistema sem IPv6: só IPv4
            self.servidor = ThreadingHTTPServer(("0.0.0.0", porta), Handler)
        self.servidor.daemon_threads = True
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()

    def publica(self, imagem):
        ok, buf = cv2.imencode(".jpg", imagem, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if ok:
            with self.trava:
                self.jpeg = buf.tobytes()
                self.trava.notify_all()


# ------------------- Trava de exposição / cor / foco (V4L2) -------------------
# A webcam ajusta brilho, cor e foco SOZINHA. Quando uma pessoa (camiseta
# escura/colorida) entra em cena, ela muda o brilho da IMAGEM INTEIRA (medido no
# teste: o piso vazio variou de 106 a 223) e a subtração de fundo vê a cena
# toda "diferente". Solução: deixar a câmera se ajustar com a cena VAZIA e
# então TRAVAR esses valores com o v4l2-ctl (pacote v4l-utils).
CONTROLES = [  # (nome do automático, valor p/ MANUAL, nome do valor manual)
    (("auto_exposure", "exposure_auto"), 1,
     ("exposure_time_absolute", "exposure_absolute")),
    (("white_balance_automatic", "white_balance_temperature_auto"), 0,
     ("white_balance_temperature",)),
    (("focus_automatic_continuous", "focus_auto"), 0, ("focus_absolute",)),
]
VALOR_AUTOMATICO = {"auto_exposure": 3, "exposure_auto": 3}   # demais: 1


def _v4l2(dev, *a):
    try:
        return subprocess.run(["v4l2-ctl", "-d", dev, *a], capture_output=True,
                              text=True, timeout=5).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _controles_existentes(dev):
    nomes = set()
    for linha in _v4l2(dev, "--list-ctrls").splitlines():
        partes = linha.split()
        if partes:
            nomes.add(partes[0])
    return nomes


def trava_camera(dev, travar):
    """travar=True: fixa exposição, cor e foco nos valores atuais.
    travar=False: devolve ao automático (p/ reajustar ao reaprender o fundo)."""
    existentes = _controles_existentes(dev)
    if not existentes:
        print("[câmera] v4l2-ctl indisponível: exposição continua automática")
        return
    feitos = []
    for autos, manual, valores in CONTROLES:
        auto = next((n for n in autos if n in existentes), None)
        valor = next((n for n in valores if n in existentes), None)
        if not auto:
            continue
        if not travar:
            _v4l2(dev, f"--set-ctrl={auto}={VALOR_AUTOMATICO.get(auto, 1)}")
            continue
        atual = None
        if valor:   # lê o valor que o automático escolheu agora
            saida = _v4l2(dev, f"--get-ctrl={valor}").strip()
            if ":" in saida:
                atual = saida.split(":")[1].strip()
        _v4l2(dev, f"--set-ctrl={auto}={manual}")
        if valor and atual:
            _v4l2(dev, f"--set-ctrl={valor}={atual}")
        feitos.append(f"{valor or auto}={atual}")
    if travar:
        print("[câmera] travada:", ", ".join(feitos) if feitos else "nenhum controle")
    else:
        print("[câmera] exposição/cor/foco de volta ao automático")


def exposicao_manual(dev, valor):
    """Fixa exposição e balanço de branco: a câmera deixa de reajustar o
    brilho quando alguém entra em cena (na Brio, o chão vazio clareava ~40%
    e a máscara ficava toda branca)."""
    existentes = _controles_existentes(dev)
    if not existentes:
        print("[câmera] v4l2-ctl indisponível: exposição continua automática")
        return
    feitos = []
    for nome, v in (("auto_exposure", 1), ("exposure_auto", 1),
                    ("exposure_time_absolute", valor), ("exposure_absolute", valor),
                    ("exposure_dynamic_framerate", 0), ("exposure_auto_priority", 0),
                    ("white_balance_automatic", 0), ("white_balance_temperature_auto", 0)):
        if nome in existentes:
            _v4l2(dev, f"--set-ctrl={nome}={v}")
            feitos.append(f"{nome}={v}")
    print("[câmera] exposição MANUAL:", ", ".join(feitos))


def abre_camera(args):
    if args.video:
        return cv2.VideoCapture(args.video)
    if sys.platform.startswith("linux"):
        # Raspberry Pi: modo validado nos testes de hardware. Em 30 fps o USB
        # da Pi 3B perde dados e os quadros chegam corrompidos.
        # (mesma ordem do captura_teste.cpp, que funcionou na Pi)
        cap = cv2.VideoCapture(args.camera, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*"YUYV"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 15)
    else:
        cap = cv2.VideoCapture(args.camera)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap


# --------------------------------- Programa ---------------------------------
def main():
    global TEMPO_CRITICO_S, COOLDOWN_ALERTA_S, QUEDA_LENTA_S
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--video", default=None, help="(opcional) arquivo de vídeo")
    ap.add_argument("--teste", action="store_true", help="tempo crítico de 5 s")
    ap.add_argument("--exposicao", type=int, default=None, metavar="N",
                    help="exposição MANUAL fixa (v4l2 exposure_time_absolute, "
                         "em unidades de 100 us; ex.: 150 = 15 ms). Desliga a "
                         "exposição e o balanço de branco automáticos.")
    ap.add_argument("--travar", action="store_true",
                    help="(experimental) trava exposição/cor/foco via v4l2-ctl. "
                         "Na LifeCam deixou a imagem estourada e desfocada.")
    ap.add_argument("--gravar", default=None, metavar="ARQUIVO.avi",
                    help="grava a imagem CRUA da câmera durante o teste ao vivo")
    ap.add_argument("--web", type=int, default=None, metavar="PORTA",
                    help="sem janelas: transmite a imagem para o navegador")
    args = ap.parse_args()
    if args.teste:
        TEMPO_CRITICO_S = 5.0
        QUEDA_LENTA_S = 8.0          # no teste, queda lenta após 8 s no chão
        COOLDOWN_ALERTA_S = 20.0     # no teste, alertas seguidos não ficam bloqueados 5 min
        print("[MODO TESTE] tempo crítico = 5 s")

    cap = abre_camera(args)
    if not cap.isOpened():
        print("Erro: não foi possível abrir a câmera.")
        return
    fps_video = cap.get(cv2.CAP_PROP_FPS) if args.video else None

    web = None
    if args.web:
        web = Transmissor(args.web)
        print(f"Imagem disponível no navegador: http://yuri-pi.local:{args.web}")
        print("(Ctrl+C neste terminal para encerrar)")

    def on_evento(tipo, info):
        print(f"[EVENTO] {tipo.upper()} ({info['tipo']}) | transição {info['transicao_s']} s | "
              f"{info['tempo_no_chao_s']} s no chão | "
              f"{'IMÓVEL' if info['imovel'] else 'movendo-se'} "
              f"(mov={info['movimento']})")
        if tipo == "queda_grave":
            foto = os.path.join(tempfile.gettempdir(), "queda.jpg")
            cv2.imwrite(foto, on_evento.quadro)
            print(f"[EVENTO] foto salva em {foto}")
    on_evento.quadro = None

    sil = Silhueta(compensar=args.exposicao is None)
    fsm = FSM(on_evento)
    print("Deixe a cena VAZIA por 6 s (câmera se ajusta e o fundo é aprendido)...")

    try:
        laco(cap, sil, fsm, on_evento, web, fps_video, args)
    except KeyboardInterrupt:
        print("\nEncerrado.")
    if sil.total_quadros:
        print(f"[câmera] quadros corrompidos descartados: {sil.total_descartados} "
              f"de {sil.total_quadros} "
              f"({100 * sil.total_descartados / sil.total_quadros:.1f}%)")
    if laco.gravador is not None:
        laco.gravador.release()
        print(f"[gravação] arquivo fechado: {args.gravar}")
    cv2.destroyAllWindows()


def laco(cap, sil, fsm, on_evento, web, fps_video, args):
    t_aprender = None
    t_fundo_mudou = None
    n = 0
    falhas = 0
    # trava de exposição só faz sentido com câmera de verdade no Linux (Pi)
    dev = (f"/dev/video{args.camera}"
           if sys.platform.startswith("linux") and not fps_video else None)
    travada = False
    if dev:
        # SEMPRE devolve a câmera ao automático ao iniciar: as configurações
        # do v4l2 ficam gravadas na câmera enquanto ela estiver ligada, e uma
        # execução anterior pode tê-la deixado travada em valores ruins.
        if args.exposicao is not None:
            exposicao_manual(dev, args.exposicao)
        else:
            trava_camera(dev, False)
    while True:
        ok, quadro = cap.read()
        if not ok:
            if fps_video:            # fim do arquivo de vídeo
                break
            # Câmera sem quadro: pode estar inicializando ou ter caído do USB.
            # Espera e, se persistir (~3 s), fecha e REABRE a câmera, em vez
            # de encerrar o programa.
            falhas += 1
            time.sleep(0.1)
            if falhas % 30 == 0:
                print("[câmera] sem imagem; tentando reabrir...")
                cap.release()
                time.sleep(1.0)
                cap = abre_camera(args)
                t_aprender = None    # fundo precisa ser reaprendido
                sil.reinicia()
                if dev and args.exposicao is None:
                    trava_camera(dev, False)
                    travada = False
                elif dev:
                    exposicao_manual(dev, args.exposicao)
            continue
        if falhas >= 30:
            print("[câmera] reconectada. Deixe a cena VAZIA por 6 s...")
        falhas = 0
        n += 1
        t = n / fps_video if fps_video else time.monotonic()
        if t_aprender is None:
            t_aprender = t

        decorrido = t - t_aprender
        aquecendo = decorrido < AQUECIMENTO_S
        aprendendo = not aquecendo and decorrido < AQUECIMENTO_S + APRENDER_FUNDO_S
        on_evento.quadro = quadro
        if args.gravar:
            if laco.gravador is None:
                h, w = quadro.shape[:2]
                laco.gravador = cv2.VideoWriter(
                    args.gravar, cv2.VideoWriter.fourcc(*"MJPG"), 15, (w, h))
                print(f"[gravação] salvando a câmera em {args.gravar}")
            laco.gravador.write(quadro)
        if dev and args.travar and not aquecendo and not travada:
            # câmera já se ajustou com a cena vazia: trava antes de aprender
            trava_camera(dev, True)
            travada = True

        if aquecendo:
            # câmera ainda ajustando foco/exposição: não aprende nada ainda
            peq = cv2.resize(quadro, (LARG, ALT))
            mascara = np.zeros((ALT, LARG), np.uint8)
            m = Medida()
        else:
            # fundo: aprende rápido no início; devagar SÓ com a cena vazia;
            # CONGELADO enquanto houver alguém em cena ou queda em andamento.
            # (Teste de 17/11: a pessoa sentada ~20 s em IDLE foi sendo
            #  absorvida pelo fundo e, ao deitar, a silhueta saiu partida.)
            if aprendendo:
                taxa = -1
            elif fsm.estado == Estado.IDLE and not laco.alguem_em_cena:
                taxa = TAXA_APRENDIZADO
            else:
                taxa = 0.0
            peq, mascara, m = sil.processa(quadro, taxa)
            # "alguém em cena" com folga de 3 s (evita reabrir o aprendizado
            # num quadro em que a mancha falhou por um instante)
            if m.detectado:
                laco.t_visto = t
            laco.alguem_em_cena = t - laco.t_visto < 3.0
            if not aprendendo and not m.descartado:
                fsm.passo(m, t)

        # Fundo errado por muito tempo (luz mudou, câmera mexeu): reaprende
        # sozinho, mas só fora de uma queda em andamento.
        auto_reaprender = False
        if m.fundo_mudou and not aprendendo and m.mov_global < IMAGEM_PARADA:
            t_fundo_mudou = t_fundo_mudou or t
            if fsm.estado == Estado.IDLE and t - t_fundo_mudou >= FUNDO_MUDOU_S:
                auto_reaprender = True
                print("[fundo] imagem mudou demais; reaprendendo o fundo...")
        else:
            t_fundo_mudou = None

        # ----------------------------- tela -----------------------------
        tela = peq.copy()
        if aquecendo:
            texto, cor = "AQUECENDO CAMERA - saia da cena", (0, 200, 255)
        elif aprendendo:
            texto, cor = "APRENDENDO FUNDO - saia da cena", (0, 200, 255)
        elif m.fundo_mudou:
            texto, cor = "FUNDO MUDOU - reaprendendo em instantes", (0, 200, 255)
        else:
            cor = (0, 200, 0) if fsm.estado == Estado.IDLE else (0, 0, 255)
            texto = fsm.estado.value
            if m.detectado:
                em_pe, deitado = fsm.classifica(m)
                pos = ("EM PE" if em_pe else "DEITADO" if deitado
                       else "NA BORDA" if m.borda else "?")
                ref = f"{m.area / fsm.area_ref:.1f}x" if fsm.area_ref else "-"
                texto += f" | {pos} | along {m.along:.1f} | area {ref}"
                cv2.drawContours(tela, [m.contorno], -1, (0, 255, 0), 1)
                caixa = cv2.boxPoints(m.retangulo).astype(np.int32)
                cv2.drawContours(tela, [caixa], -1, cor, 2)
        tela = cv2.resize(tela, (640, 480))
        cv2.putText(tela, texto, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)

        reaprender = auto_reaprender
        if web:
            # câmera e máscara lado a lado, em tamanho reduzido p/ a rede
            masc = cv2.cvtColor(cv2.resize(mascara, (640, 480)), cv2.COLOR_GRAY2BGR)
            web.publica(cv2.resize(cv2.hconcat([tela, masc]), (960, 360)))
            if web.pedir_fundo:
                web.pedir_fundo = False
                reaprender = True
        else:
            cv2.imshow("Silhueta - camera", tela)
            cv2.imshow("Silhueta - mascara", mascara)
            tecla = cv2.waitKey(1) & 0xFF
            if tecla == ord("q"):
                break
            reaprender = reaprender or tecla == ord("b")

        if reaprender:
            sil.reinicia()
            fsm = FSM(on_evento)
            t_aprender = None
            if dev and args.exposicao is None:   # destrava e deixa reajustar
                trava_camera(dev, False)
                travada = False
            print("Reaprendendo o fundo: deixe a cena VAZIA por 6 s...")


laco.gravador = None
laco.alguem_em_cena = False
laco.t_visto = -1e9


if __name__ == "__main__":
    main()
