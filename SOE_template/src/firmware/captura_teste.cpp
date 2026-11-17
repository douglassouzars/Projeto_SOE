// captura_teste.cpp — Projeto Alerta de Queda (SOE)
//
// Primeiro passo do firmware: valida a captura da câmera na Raspberry Pi.
//   - abre a webcam pelo V4L2 em 640x480, formato YUYV, 15 fps
//     (configuração validada nos testes de hardware: em 30 fps o USB
//      da Pi 3B perde pacotes e os quadros chegam corrompidos);
//   - uma thread CAPTURA quadros sem parar (produtora);
//   - a thread principal CONSOME o quadro mais recente (no projeto final,
//     é aqui que entra o detector de quedas);
//   - mede e imprime o FPS de captura e de consumo a cada 2 s;
//   - salva uma foto no início e outra no fim, para conferir a imagem;
//   - encerra de forma limpa com Ctrl+C (SIGINT) ou SIGTERM.
//
// Uso:
//   ./build/captura_teste                 -> câmera /dev/video0
//   ./build/captura_teste /dev/video2     -> outra câmera
//   ./build/captura_teste queda.mp4       -> arquivo de vídeo (testes)

#include <opencv2/opencv.hpp>

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <csignal>
#include <cstdio>
#include <cstring>
#include <mutex>
#include <string>
#include <thread>

using Relogio = std::chrono::steady_clock;

// ---------------------------- configuração ----------------------------
static const int LARGURA = 640;
static const int ALTURA = 480;
static const int FPS_CAMERA = 15;
static const int QUADROS_DESCARTADOS = 45;  // ~3 s a 15 fps: tempo p/ o foco

// ------------------------- encerramento limpo -------------------------
// Variável lida por todas as threads; o tratador de sinal só a zera.
static std::atomic<bool> executando{true};

static void trata_sinal(int) { executando = false; }

static void instala_tratadores() {
    struct sigaction sa;
    std::memset(&sa, 0, sizeof sa);
    sa.sa_handler = trata_sinal;
    sigemptyset(&sa.sa_mask);  // sem SA_RESTART: esperas bloqueantes retornam
    sigaction(SIGINT, &sa, nullptr);
    sigaction(SIGTERM, &sa, nullptr);
}

// ------------------- quadro compartilhado entre threads ----------------
// A captura sempre sobrescreve o quadro mais recente. Se o consumidor for
// mais lento que a câmera (o que acontecerá com o detector na Pi 3B), os
// quadros intermediários são descartados: o detector sempre analisa a cena
// mais atual, sem acumular atraso.
struct QuadroCompartilhado {
    std::mutex trava;
    std::condition_variable novo_quadro;
    cv::Mat quadro;
    unsigned long sequencia = 0;  // incrementa a cada quadro capturado
};

static std::atomic<unsigned long> total_capturados{0};

static void thread_captura(cv::VideoCapture& camera, QuadroCompartilhado& compartilhado) {
    cv::Mat quadro;
    int falhas_seguidas = 0;

    while (executando) {
        if (!camera.read(quadro) || quadro.empty()) {
            if (++falhas_seguidas >= 30) {  // ~2 s sem imagem: desiste
                std::fprintf(stderr, "[captura] câmera parou de responder\n");
                executando = false;
                break;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
            continue;
        }
        falhas_seguidas = 0;

        {
            std::lock_guard<std::mutex> lk(compartilhado.trava);
            cv::swap(quadro, compartilhado.quadro);  // troca sem copiar pixels
            compartilhado.sequencia++;
        }
        compartilhado.novo_quadro.notify_one();
        total_capturados++;
    }
    compartilhado.novo_quadro.notify_all();  // acorda o consumidor p/ sair
}

// ------------------------------- abertura -------------------------------
static bool eh_camera(const std::string& origem) {
    return origem.rfind("/dev/video", 0) == 0;
}

static bool abre_origem(cv::VideoCapture& camera, const std::string& origem) {
    if (!eh_camera(origem))  // arquivo de vídeo
        return camera.open(origem);

    if (!camera.open(origem, cv::CAP_V4L2))
        return false;

    // Pede o modo à câmera: a redução de resolução acontece no hardware
    // dela, antes do USB (é o que alivia o barramento da Pi).
    camera.set(cv::CAP_PROP_FOURCC, cv::VideoWriter::fourcc('Y', 'U', 'Y', 'V'));
    camera.set(cv::CAP_PROP_FRAME_WIDTH, LARGURA);
    camera.set(cv::CAP_PROP_FRAME_HEIGHT, ALTURA);
    camera.set(cv::CAP_PROP_FPS, FPS_CAMERA);
    

    // Descarta os primeiros quadros (podem vir escuros, desfocados ou
    // corrompidos enquanto a câmera inicializa).
    cv::Mat descarte;
    for (int i = 0; i < QUADROS_DESCARTADOS && executando; i++)
        camera.read(descarte);
    return true;
}

static std::string formato_texto(double fourcc) {
    int f = static_cast<int>(fourcc);
    char s[5] = {static_cast<char>(f & 0xFF), static_cast<char>((f >> 8) & 0xFF),
                 static_cast<char>((f >> 16) & 0xFF), static_cast<char>((f >> 24) & 0xFF), 0};
    return s;
}

// --------------------------------- main ---------------------------------
int main(int argc, char** argv) {
    const std::string origem = (argc > 1) ? argv[1] : "/dev/video0";
    instala_tratadores();

    cv::VideoCapture camera;
    if (!abre_origem(camera, origem)) {
        std::fprintf(stderr, "Erro: não foi possível abrir '%s'\n", origem.c_str());
        return 1;
    }

    // Confere o modo que a câmera REALMENTE aceitou (pode diferir do pedido).
    std::printf("Origem : %s\n", origem.c_str());
    std::printf("Modo   : %.0fx%.0f, formato %s, %.0f fps (informado pelo driver)\n",
                camera.get(cv::CAP_PROP_FRAME_WIDTH), camera.get(cv::CAP_PROP_FRAME_HEIGHT),
                formato_texto(camera.get(cv::CAP_PROP_FOURCC)).c_str(),
                camera.get(cv::CAP_PROP_FPS));
    std::printf("Ctrl+C para encerrar.\n\n");

    QuadroCompartilhado compartilhado;
    std::thread captura(thread_captura, std::ref(camera), std::ref(compartilhado));

    // ---- consumidor: no projeto final, aqui roda o detector de quedas ----
    cv::Mat atual;
    unsigned long ultima_sequencia = 0, consumidos = 0;
    unsigned long capturados_antes = 0, consumidos_antes = 0;
    bool foto_inicial_salva = false;
    auto inicio_janela = Relogio::now();

    while (executando) {
        {
            std::unique_lock<std::mutex> lk(compartilhado.trava);
            compartilhado.novo_quadro.wait_for(lk, std::chrono::seconds(1), [&] {
                return compartilhado.sequencia != ultima_sequencia || !executando;
            });
            if (!executando) break;
            if (compartilhado.sequencia == ultima_sequencia) continue;  // timeout
            compartilhado.quadro.copyTo(atual);
            ultima_sequencia = compartilhado.sequencia;
        }
        consumidos++;

        if (!foto_inicial_salva) {
            cv::imwrite("captura_inicio.jpg", atual);
            std::printf("Foto inicial salva em captura_inicio.jpg (%dx%d)\n",
                        atual.cols, atual.rows);
            foto_inicial_salva = true;
        }

        // Relatório de desempenho a cada 2 s.
        double dt = std::chrono::duration<double>(Relogio::now() - inicio_janela).count();
        if (dt >= 2.0) {
            unsigned long cap = total_capturados.load();
            std::printf("FPS captura: %5.1f | FPS consumo: %5.1f | total: %lu quadros\n",
                        (cap - capturados_antes) / dt, (consumidos - consumidos_antes) / dt, cap);
            std::fflush(stdout);
            capturados_antes = cap;
            consumidos_antes = consumidos;
            inicio_janela = Relogio::now();
        }
    }

    // ------------------------- encerramento -------------------------
    executando = false;
    compartilhado.novo_quadro.notify_all();
    captura.join();  // espera a thread de captura terminar

    if (!atual.empty()) {
        cv::imwrite("captura_fim.jpg", atual);
        std::printf("\nFoto final salva em captura_fim.jpg\n");
    }
    camera.release();
    std::printf("Encerrado: %lu quadros capturados, %lu consumidos.\n",
                total_capturados.load(), consumidos);
    return 0;
}
