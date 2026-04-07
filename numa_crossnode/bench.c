/*
 * NUMA cross-node memory benchmark.
 *
 * Measures bandwidth (sequential read/write) and latency (pointer chase)
 * for a given buffer size.  Intended to be run under numactl so that the
 * CPU is pinned to one NUMA node and the allocation is forced to another.
 *
 * Usage:
 *   numactl --cpunodebind=0 --membind=1 ./bench -m bandwidth_read -b 67108864
 *   numactl --cpunodebind=0 --membind=1 ./bench -m latency       -b 67108864
 *
 * Build:
 *   gcc -O2 -o bench bench.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include <getopt.h>

/* ------------------------------------------------------------------ */
/*  Timing helpers                                                     */
/* ------------------------------------------------------------------ */

static double now_sec(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

/* ------------------------------------------------------------------ */
/*  Bandwidth: sequential read                                         */
/* ------------------------------------------------------------------ */

static double bandwidth_read(volatile char *buf, size_t len, int reps)
{
    volatile char sink = 0;
    double t0 = now_sec();
    for (int r = 0; r < reps; r++) {
        for (size_t i = 0; i < len; i += 64)
            sink += buf[i];          /* one load per cache line */
    }
    double elapsed = now_sec() - t0;
    (void)sink;
    return (double)len * reps / elapsed;   /* bytes/sec */
}

/* ------------------------------------------------------------------ */
/*  Bandwidth: sequential write                                        */
/* ------------------------------------------------------------------ */

static double bandwidth_write(volatile char *buf, size_t len, int reps)
{
    double t0 = now_sec();
    for (int r = 0; r < reps; r++) {
        for (size_t i = 0; i < len; i += 64)
            buf[i] = (char)i;
    }
    double elapsed = now_sec() - t0;
    return (double)len * reps / elapsed;
}

/* ------------------------------------------------------------------ */
/*  Latency: pointer chase                                             */
/* ------------------------------------------------------------------ */

/*
 * Build a random cyclic permutation of indices spaced by `stride` bytes,
 * then chase pointers and measure average access latency.
 */
/*
 * The pointer-chase loop must not be optimised away or unrolled into
 * prefetch-friendly patterns.  We put it in its own noinline function
 * and use an asm volatile barrier after each load.
 */
static void *chase_sink;

static __attribute__((noinline)) void *
do_chase(void *start, size_t steps)
{
    void *p = start;
    for (size_t i = 0; i < steps; i++) {
        p = *(void **)p;
        __asm__ volatile("" : "+r"(p) :: "memory");
    }
    return p;
}

static double latency_chase(char *buf, size_t len)
{
    size_t stride = 64;                        /* cache-line sized steps */
    size_t n = len / stride;
    if (n < 2)
        return 0.0;

    /* Build a random full-cycle permutation (Fisher-Yates). */
    size_t *order = malloc(n * sizeof *order);
    if (!order) { perror("malloc"); exit(1); }
    for (size_t i = 0; i < n; i++)
        order[i] = i;
    srand(42);
    for (size_t i = n - 1; i > 0; i--) {
        size_t j = (size_t)rand() % (i + 1);
        size_t tmp = order[i];
        order[i] = order[j];
        order[j] = tmp;
    }

    /* Write next-pointers into the buffer so buf[order[k]] points to
       buf[order[k+1]], forming a single Hamiltonian cycle.              */
    for (size_t k = 0; k < n; k++) {
        size_t cur  = order[k];
        size_t next = order[(k + 1) % n];
        *(void **)(buf + cur * stride) = (void *)(buf + next * stride);
    }
    free(order);

    /* Warm up — traverse the full cycle once */
    chase_sink = do_chase(buf, n);

    /* Timed chase — aim for >=0.5 s of measurement */
    size_t total_steps = n * 64;
    if (total_steps < 2000000) total_steps = 2000000;

    double t0 = now_sec();
    chase_sink = do_chase(buf, total_steps);
    double elapsed = now_sec() - t0;

    return elapsed / (double)total_steps * 1e9;   /* nanoseconds per access */
}

/* ------------------------------------------------------------------ */
/*  main                                                               */
/* ------------------------------------------------------------------ */

static void usage(const char *prog)
{
    fprintf(stderr,
        "Usage: %s -m <mode> -b <buffer_bytes> [-r <reps>]\n"
        "  mode:  bandwidth_read | bandwidth_write | latency\n"
        "  buffer_bytes:  working-set size in bytes  (e.g. 67108864 = 64 MiB)\n"
        "  reps:  repetitions for bandwidth tests  (default: auto)\n",
        prog);
    exit(1);
}

int main(int argc, char **argv)
{
    const char *mode = NULL;
    size_t bufsize  = 0;
    int    reps     = 0;

    int opt;
    while ((opt = getopt(argc, argv, "m:b:r:h")) != -1) {
        switch (opt) {
        case 'm': mode    = optarg;              break;
        case 'b': bufsize = (size_t)atol(optarg); break;
        case 'r': reps    = atoi(optarg);         break;
        default:  usage(argv[0]);
        }
    }
    if (!mode || bufsize == 0)
        usage(argv[0]);

    /* Auto-select reps so total data touched is ~2 GiB */
    if (reps <= 0) {
        size_t target = (size_t)2 << 30;   /* 2 GiB */
        reps = (int)(target / bufsize);
        if (reps < 1) reps = 1;
        if (reps > 2000) reps = 2000;
    }

    /* Allocate and fault the pages */
    char *buf = malloc(bufsize);
    if (!buf) { perror("malloc"); return 1; }
    memset(buf, 0xAA, bufsize);

    double result = 0.0;
    const char *unit = "";

    if (strcmp(mode, "bandwidth_read") == 0) {
        result = bandwidth_read((volatile char *)buf, bufsize, reps) / (1024.0 * 1024.0);
        unit = "MiB/s";
    } else if (strcmp(mode, "bandwidth_write") == 0) {
        result = bandwidth_write((volatile char *)buf, bufsize, reps) / (1024.0 * 1024.0);
        unit = "MiB/s";
    } else if (strcmp(mode, "latency") == 0) {
        result = latency_chase(buf, bufsize);
        unit = "ns";
    } else {
        fprintf(stderr, "Unknown mode: %s\n", mode);
        free(buf);
        return 1;
    }

    free(buf);

    /* Machine-readable output to stdout */
    printf("%.4f %s\n", result, unit);

    return 0;
}
