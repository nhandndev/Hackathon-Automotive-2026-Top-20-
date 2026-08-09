// Minimal AF_VSOCK TCP-style relay for Android guest hotfix.
//
// It listens on one vsock CID/port and forwards every accepted connection to a
// target vsock CID/port. Intended for:
//   listen  cid 1 port 9210  -> target cid 2 port 9300

#include <arpa/inet.h>
#include <errno.h>
#include <linux/vm_sockets.h>
#include <netinet/in.h>
#include <pthread.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

#ifndef VMADDR_CID_ANY
#define VMADDR_CID_ANY 0xFFFFFFFFU
#endif

typedef struct {
    int from_fd;
    int to_fd;
    const char *name;
} pump_args_t;

typedef struct {
    int client_fd;
    uint32_t target_cid;
    uint32_t target_port;
} conn_args_t;

static uint32_t parse_u32(const char *s, const char *name) {
    char *end = NULL;
    unsigned long v = strtoul(s, &end, 0);
    if (!s || *s == '\0' || !end || *end != '\0' || v > UINT32_MAX) {
        fprintf(stderr, "invalid %s: %s\n", name, s ? s : "(null)");
        exit(2);
    }
    return (uint32_t)v;
}

static void usage(const char *argv0) {
    fprintf(stderr,
            "usage: %s --listen-cid CID --listen-port PORT --target-cid CID --target-port PORT\n",
            argv0);
}

static int make_vsock_listener(uint32_t cid, uint32_t port) {
    int fd = socket(AF_VSOCK, SOCK_STREAM, 0);
    if (fd < 0) {
        perror("socket listen AF_VSOCK");
        return -1;
    }

    int one = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));

    struct sockaddr_vm addr;
    memset(&addr, 0, sizeof(addr));
    addr.svm_family = AF_VSOCK;
    addr.svm_cid = cid;
    addr.svm_port = port;

    if (bind(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind listen AF_VSOCK");
        close(fd);
        return -1;
    }

    if (listen(fd, 16) < 0) {
        perror("listen AF_VSOCK");
        close(fd);
        return -1;
    }
    return fd;
}

static int connect_vsock(uint32_t cid, uint32_t port) {
    int fd = socket(AF_VSOCK, SOCK_STREAM, 0);
    if (fd < 0) {
        perror("socket target AF_VSOCK");
        return -1;
    }

    struct sockaddr_vm addr;
    memset(&addr, 0, sizeof(addr));
    addr.svm_family = AF_VSOCK;
    addr.svm_cid = cid;
    addr.svm_port = port;

    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("connect target AF_VSOCK");
        close(fd);
        return -1;
    }
    return fd;
}

static void *pump(void *raw) {
    pump_args_t *args = (pump_args_t *)raw;
    char buf[16384];

    for (;;) {
        ssize_t n = read(args->from_fd, buf, sizeof(buf));
        if (n == 0) break;
        if (n < 0) {
            if (errno == EINTR) continue;
            perror(args->name);
            break;
        }

        ssize_t off = 0;
        while (off < n) {
            ssize_t w = write(args->to_fd, buf + off, (size_t)(n - off));
            if (w < 0) {
                if (errno == EINTR) continue;
                perror(args->name);
                goto done;
            }
            off += w;
        }
    }

done:
    shutdown(args->to_fd, SHUT_WR);
    return NULL;
}

static void *handle_conn(void *raw) {
    conn_args_t *args = (conn_args_t *)raw;
    int client_fd = args->client_fd;
    int target_fd = connect_vsock(args->target_cid, args->target_port);
    free(args);

    if (target_fd < 0) {
        close(client_fd);
        return NULL;
    }

    fprintf(stderr, "vhal-vsock-relay: connected client -> target\n");

    pump_args_t a = { client_fd, target_fd, "client->target" };
    pump_args_t b = { target_fd, client_fd, "target->client" };
    pthread_t ta;
    pthread_t tb;
    pthread_create(&ta, NULL, pump, &a);
    pthread_create(&tb, NULL, pump, &b);
    pthread_join(ta, NULL);
    pthread_join(tb, NULL);

    close(client_fd);
    close(target_fd);
    fprintf(stderr, "vhal-vsock-relay: connection closed\n");
    return NULL;
}

int main(int argc, char **argv) {
    uint32_t listen_cid = VMADDR_CID_ANY;
    uint32_t listen_port = 0;
    uint32_t target_cid = 0;
    uint32_t target_port = 0;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--listen-cid") == 0 && i + 1 < argc) {
            listen_cid = parse_u32(argv[++i], "listen-cid");
        } else if (strcmp(argv[i], "--listen-port") == 0 && i + 1 < argc) {
            listen_port = parse_u32(argv[++i], "listen-port");
        } else if (strcmp(argv[i], "--target-cid") == 0 && i + 1 < argc) {
            target_cid = parse_u32(argv[++i], "target-cid");
        } else if (strcmp(argv[i], "--target-port") == 0 && i + 1 < argc) {
            target_port = parse_u32(argv[++i], "target-port");
        } else {
            usage(argv[0]);
            return 2;
        }
    }

    if (!listen_port || !target_port) {
        usage(argv[0]);
        return 2;
    }

    signal(SIGPIPE, SIG_IGN);

    int listen_fd = make_vsock_listener(listen_cid, listen_port);
    if (listen_fd < 0) return 1;

    fprintf(stderr, "vhal-vsock-relay: listening cid=%u port=%u -> cid=%u port=%u\n",
            listen_cid, listen_port, target_cid, target_port);

    for (;;) {
        int client_fd = accept(listen_fd, NULL, NULL);
        if (client_fd < 0) {
            if (errno == EINTR) continue;
            perror("accept");
            break;
        }

        conn_args_t *args = calloc(1, sizeof(*args));
        if (!args) {
            close(client_fd);
            continue;
        }
        args->client_fd = client_fd;
        args->target_cid = target_cid;
        args->target_port = target_port;

        pthread_t tid;
        if (pthread_create(&tid, NULL, handle_conn, args) == 0) {
            pthread_detach(tid);
        } else {
            perror("pthread_create");
            close(client_fd);
            free(args);
        }
    }

    close(listen_fd);
    return 1;
}
