cmake_minimum_required(VERSION 3.16)
project(alerta_queda LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)   # otimizado (-O3): importa na Pi 3B
endif()

find_package(OpenCV REQUIRED COMPONENTS core imgproc imgcodecs videoio)
find_package(Threads REQUIRED)

# Teste de captura da câmera (etapa 1 do firmware)
add_executable(captura_teste captura_teste.cpp)
target_link_libraries(captura_teste PRIVATE ${OpenCV_LIBS} Threads::Threads)
target_compile_options(captura_teste PRIVATE -Wall -Wextra)
