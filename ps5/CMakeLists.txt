cmake_minimum_required(VERSION 3.20)
project(ps5_error_analyzer C ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

if(NOT DEFINED PS5SDK)
  message(FATAL_ERROR "Set PS5SDK to the root of the PS5Dev PS5SDK checkout")
endif()

add_executable(ps5_error_analyzer source/main.c)
set_target_properties(ps5_error_analyzer PROPERTIES
  OUTPUT_NAME "ps5_error_analyzer.elf"
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/bin")

target_include_directories(ps5_error_analyzer PRIVATE "${PS5SDK}" "${PS5SDK}/include")
target_link_directories(ps5_error_analyzer PRIVATE "${PS5SDK}/lib")
target_link_libraries(ps5_error_analyzer PRIVATE ps5sdk_crt)

# Use the SDK's linker script while allowing SDK/repository paths with spaces.
set(CMAKE_EXE_LINKER_FLAGS "-fuse-ld=lld")
target_link_options(ps5_error_analyzer PRIVATE
  "LINKER:-T,${PS5SDK}/linker.x"
  "LINKER:--build-id=none"
  "LINKER:-z,norelro")

if(NOT CMAKE_C_COMPILER_ID MATCHES "Clang")
  message(FATAL_ERROR "PS5SDK payloads must be built with Clang")
endif()

