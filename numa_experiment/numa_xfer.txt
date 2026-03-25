/*
 * numa_xfer.c — Minimal NUMA memory transfer benchmark for DOE experiments.
 *
 * Allocates a buffer, performs memcpy or non-temporal stores across it using
 * multiple threads, and reports bandwidth (GB/s) and latency (ns/cacheline).
 *
 * Build:
 *   gcc -O2 -march=native -o numa_xfer numa_xfer.c -lpthread -lm
 *
 * Usage:
 *   ./numa_xfer --mode memcpy --threads 24 --bytes 536870912 --iterations 10 --json
 *   ./numa_xfer --mode ntstore --threads 1 --bytes 1048576 --iterations 10 --json
 *
 * Designed to be wrapped by numactl for NUMA node pinning:
 *   numactl --cpunodebind=1 --membind=0 ./numa_xfer --mode memcpy ...
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <time.h>
#include <pthread.h>
#include <getopt.h>
#include <immintrin.h>

#define CACHELINE_SIZE 64

typedef struct {
    char *src;
    char *dst;
    size_t bytes;
    int use_ntstore;
    int iterations;
    double elapsed_sec;
} thread_arg_t;

static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

static void do_memcpy(char *dst, const char *src, size_t n) {
    memcpy(dst, src, n);
}

static void do_ntstore(char *dst, const char *src, size_t n) {
#ifdef __AVX2__
    size_t i;
    for (i = 0; i + 32 <= n; i += 32) {
        __m256i v = _mm256_load_si256((const __m256i *)(src + i));
        _mm256_stream_si256((__m256i *)(dst + i), v);
    }
    _mm_sfence();
    /* Handle remainder */
    if (i < n) memcpy(dst + i, src + i, n - i);
#else
    /* Fallback: plain memcpy if no AVX2 */
    memcpy(dst, src, n);
#endif
}

static void *worker(void *arg) {
    thread_arg_t *t = (thread_arg_t *)arg;
    double start = now_sec();

    for (int iter = 0; iter < t->iterations; iter++) {
        if (t->use_ntstore)
            do_ntstore(t->dst, t->src, t->bytes);
        else
            do_memcpy(t->dst, t->src, t->bytes);
    }

    t->elapsed_sec = now_sec() - start;
    return NULL;
}

static void usage(const char *prog) {
    fprintf(stderr,
        "Usage: %s --mode memcpy|ntstore --threads N --bytes N --iterations N [--json] [--quiet] [--hugepages]\n",
        prog);
    exit(1);
}

int main(int argc, char **argv) {
    int nthreads = 1;
    size_t total_bytes = 1048576;
    int iterations = 10;
    int use_ntstore = 0;
    int json_output = 0;
    int quiet = 0;

    static struct option long_opts[] = {
        {"mode",       required_argument, 0, 'm'},
        {"threads",    required_argument, 0, 't'},
        {"bytes",      required_argument, 0, 'b'},
        {"iterations", required_argument, 0, 'i'},
        {"json",       no_argument,       0, 'j'},
        {"quiet",      no_argument,       0, 'q'},
        {"hugepages",  no_argument,       0, 'h'},
        {0, 0, 0, 0}
    };

    int opt;
    while ((opt = getopt_long(argc, argv, "", long_opts, NULL)) != -1) {
        switch (opt) {
            case 'm': use_ntstore = (strcmp(optarg, "ntstore") == 0); break;
            case 't': nthreads = atoi(optarg); break;
            case 'b': total_bytes = (size_t)atol(optarg); break;
            case 'i': iterations = atoi(optarg); break;
            case 'j': json_output = 1; break;
            case 'q': quiet = 1; break;
            case 'h': /* hugepages — handled by numactl/mmap, accepted but ignored */ break;
            default:  usage(argv[0]);
        }
    }

    if (nthreads < 1) nthreads = 1;
    if (total_bytes < 64) total_bytes = 64;
    if (iterations < 1) iterations = 1;

    /* Ensure alignment for AVX2 streaming stores */
    size_t aligned_bytes = (total_bytes + 31) & ~(size_t)31;
    size_t per_thread = aligned_bytes / nthreads;
    if (per_thread < 64) per_thread = 64;

    /* Allocate aligned source and destination buffers */
    char *src = NULL, *dst = NULL;
    if (posix_memalign((void **)&src, 64, per_thread * nthreads) != 0 ||
        posix_memalign((void **)&dst, 64, per_thread * nthreads) != 0) {
        fprintf(stderr, "ERROR: Failed to allocate %zu bytes\n", per_thread * nthreads);
        return 1;
    }

    /* Touch all pages to fault them in (important for NUMA placement) */
    memset(src, 0xAA, per_thread * nthreads);
    memset(dst, 0x00, per_thread * nthreads);

    /* Launch threads */
    pthread_t *threads = calloc(nthreads, sizeof(pthread_t));
    thread_arg_t *args = calloc(nthreads, sizeof(thread_arg_t));

    for (int i = 0; i < nthreads; i++) {
        args[i].src = src + i * per_thread;
        args[i].dst = dst + i * per_thread;
        args[i].bytes = per_thread;
        args[i].use_ntstore = use_ntstore;
        args[i].iterations = iterations;
        args[i].elapsed_sec = 0;
    }

    for (int i = 0; i < nthreads; i++)
        pthread_create(&threads[i], NULL, worker, &args[i]);

    for (int i = 0; i < nthreads; i++)
        pthread_join(threads[i], NULL);

    /* Compute aggregate bandwidth and latency */
    double max_elapsed = 0;
    for (int i = 0; i < nthreads; i++) {
        if (args[i].elapsed_sec > max_elapsed)
            max_elapsed = args[i].elapsed_sec;
    }

    double total_transferred = (double)per_thread * nthreads * iterations;
    double bandwidth_gbs = (total_transferred / (1024.0 * 1024.0 * 1024.0)) / max_elapsed;

    /* Latency: average time per cacheline access */
    size_t total_cachelines = (per_thread * nthreads * iterations) / CACHELINE_SIZE;
    double latency_ns = (max_elapsed * 1e9) / (double)total_cachelines;

    if (json_output) {
        printf("{\"bandwidth_GBs\": %.1f, \"latency_ns\": %.1f}\n", bandwidth_gbs, latency_ns);
    } else if (!quiet) {
        printf("Threads:    %d\n", nthreads);
        printf("Buffer:     %zu bytes (%.1f MB)\n", total_bytes, total_bytes / (1024.0 * 1024.0));
        printf("Mode:       %s\n", use_ntstore ? "ntstore" : "memcpy");
        printf("Iterations: %d\n", iterations);
        printf("Elapsed:    %.3f s\n", max_elapsed);
        printf("Bandwidth:  %.1f GB/s\n", bandwidth_gbs);
        printf("Latency:    %.1f ns/cacheline\n", latency_ns);
    }

    free(src);
    free(dst);
    free(threads);
    free(args);
    return 0;
}
