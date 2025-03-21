#ifndef TLS_UTILS_H
#define TLS_UTILS_H

#include <openssl/err.h>
#include <openssl/ssl.h>

SSL_CTX *create_tls_context();
void configure_tls_context(SSL_CTX *ctx);
void encrypt_message(const unsigned char *key, const unsigned char *iv,
                     const char *message, unsigned char *encrypted, int *len);
void decrypt_message(const unsigned char *key, const unsigned char *iv,
                     const unsigned char *encrypted, unsigned char *decrypted,
                     int *len);

#endif
