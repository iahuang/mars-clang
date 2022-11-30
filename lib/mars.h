#include <stdint.h>

#define int int32_t
#define long int32_t
#define uint uint32_t
#define byte char
#define HEAP_START (int*)0x10010000

int* __heap_ptr = HEAP_START;

int* m_malloc(int bytes) {
    __heap_ptr += bytes;
    return __heap_ptr - bytes;
}