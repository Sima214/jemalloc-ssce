#include "jemalloc/internal/jemalloc_preamble.h"

/*
 * The hooks are a little bit screwy -- they're not genuinely exported in the
 * sense that we want them available to end-users, but we do want them visible
 * from outside the generated library, so that we can use them in test code.
 * 
 * Sima214: No testing is done here!
 */
void (*test_hooks_arena_new_hook)() = NULL;

void (*test_hooks_libc_hook)() = NULL;
