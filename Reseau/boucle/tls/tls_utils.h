#ifndef TLS_UTILS_H
#define TLS_UTILS_H

#include <openssl/err.h>
#include <openssl/ssl.h>

// Define key and IV lengths for AES-256-CBC
#define KEY_LENGTH 32
#define IV_LENGTH 16
#define BLOCK_SIZE 16
#define HMAC_KEY_LENGTH 32
#define HMAC_LENGTH 32  // SHA256 output length
#define BUFFER_SIZE 1024

// Force l'alignement à 1 byte pour la compatibilité cross-platform
#pragma pack(push, 1)
struct final_message {
    unsigned char iv[IV_LENGTH];
    unsigned char encrypted_data[BUFFER_SIZE];
    unsigned char hmac[HMAC_LENGTH];
} __attribute__((packed));
#pragma pack(pop)

void encrypt_message(const unsigned char *key, const unsigned char *iv,
                     const char *message, unsigned char *encrypted, int *len);
void decrypt_message(const unsigned char *key, const unsigned char *iv,
                     const unsigned char *encrypted, unsigned char *decrypted,
                     int *len);
int generate_hmac(const unsigned char *hmac_key, const unsigned char *message,
                   int message_len, unsigned char *hmac);
int verify_hmac(const unsigned char *hmac_key, const unsigned char *message,
                 int message_len, const unsigned char *received_hmac);

#endif
