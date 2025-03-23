#ifdef _WIN32
    #include <windows.h>
#endif

#include "tls_utils.h"
#include <openssl/err.h>
#include <openssl/evp.h>
#include <openssl/hmac.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Définition des constantes de taille
#define BLOCK_SIZE 16

void pkcs7_pad(unsigned char *data, int *data_len, int block_size) {
    int padding_len = block_size - (*data_len % block_size);
    for (int i = 0; i < padding_len; i++) {
        data[*data_len + i] = padding_len;
    }
    *data_len += padding_len;
    printf("Padded length: %d\n", *data_len);
}

void pkcs7_unpad(unsigned char *data, int *data_len, int block_size) {
    int padding_len = data[*data_len - 1];
    printf("Padding length: %d\n", padding_len);
    *data_len -= padding_len;
}

int generate_hmac(const unsigned char *hmac_key, const unsigned char *message,
                   int message_len, unsigned char *hmac) {
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    EVP_PKEY *pkey = EVP_PKEY_new_mac_key(EVP_PKEY_HMAC, NULL, hmac_key, HMAC_KEY_LENGTH);
    int result = 1; // 1 = success, 0 = failure
    
    if (!ctx || !pkey) {
        fprintf(stderr, "Error creating HMAC context or key\n");
        result = 0;
        goto cleanup;
    }

    if (EVP_DigestSignInit(ctx, NULL, EVP_sha256(), NULL, pkey) <= 0) {
        fprintf(stderr, "Error initializing HMAC\n");
        ERR_print_errors_fp(stderr);
        result = 0;
        goto cleanup;
    }

    if (EVP_DigestSignUpdate(ctx, message, message_len) <= 0) {
        fprintf(stderr, "Error updating HMAC\n");
        ERR_print_errors_fp(stderr);
        result = 0;
        goto cleanup;
    }

    size_t hmac_len = HMAC_LENGTH;
    if (EVP_DigestSignFinal(ctx, hmac, &hmac_len) <= 0) {
        fprintf(stderr, "Error finalizing HMAC\n");
        ERR_print_errors_fp(stderr);
        result = 0;
        goto cleanup;
    }

    printf("Message length for HMAC: %d\n", message_len);
    printf("Generated HMAC: ");
    for(int i = 0; i < HMAC_LENGTH; i++) {
        printf("%02x", hmac[i]);
    }
    printf("\n");

cleanup:
    if (ctx) EVP_MD_CTX_free(ctx);
    if (pkey) EVP_PKEY_free(pkey);
    return result;
}

int verify_hmac(const unsigned char *hmac_key, const unsigned char *message,
                 int message_len, const unsigned char *received_hmac) {
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    EVP_PKEY *pkey = EVP_PKEY_new_mac_key(EVP_PKEY_HMAC, NULL, hmac_key, HMAC_KEY_LENGTH);
    int result = 1; // 1 = success, 0 = failure
    
    if (!ctx || !pkey) {
        fprintf(stderr, "Error creating HMAC context or key\n");
        result = 0;
        goto cleanup;
    }

    if (EVP_DigestSignInit(ctx, NULL, EVP_sha256(), NULL, pkey) <= 0) {
        fprintf(stderr, "Error initializing HMAC\n");
        ERR_print_errors_fp(stderr);
        result = 0;
        goto cleanup;
    }

    if (EVP_DigestSignUpdate(ctx, message, message_len) <= 0) {
        fprintf(stderr, "Error updating HMAC\n");
        ERR_print_errors_fp(stderr);
        result = 0;
        goto cleanup;
    }

    size_t hmac_len = HMAC_LENGTH;
    unsigned char calculated_hmac[HMAC_LENGTH];
    if (EVP_DigestSignFinal(ctx, calculated_hmac, &hmac_len) <= 0) {
        fprintf(stderr, "Error finalizing HMAC\n");
        ERR_print_errors_fp(stderr);
        result = 0;
        goto cleanup;
    }

    printf("Message length for HMAC: %d\n", message_len);
    printf("Calculated HMAC: ");
    for(int i = 0; i < HMAC_LENGTH; i++) {
        printf("%02x", calculated_hmac[i]);
    }
    printf("\nReceived HMAC: ");
    for(int i = 0; i < HMAC_LENGTH; i++) {
        printf("%02x", received_hmac[i]);
    }
    printf("\n");

    result = memcmp(calculated_hmac, received_hmac, HMAC_LENGTH) == 0;

cleanup:
    if (ctx) EVP_MD_CTX_free(ctx);
    if (pkey) EVP_PKEY_free(pkey);
    return result;
}

void encrypt_message(const unsigned char *key, const unsigned char *iv,
                     const char *message, unsigned char *encrypted, int *len) {
    EVP_CIPHER_CTX *ctx;
    int ciphertext_len = 0;
    int plaintext_len = strlen(message);
    unsigned char *padded_message = malloc(plaintext_len + BLOCK_SIZE);

    memcpy(padded_message, message, plaintext_len);
    pkcs7_pad(padded_message, &plaintext_len, BLOCK_SIZE);

    if (!(ctx = EVP_CIPHER_CTX_new())) {
        ERR_print_errors_fp(stderr);
        free(padded_message);
        exit(EXIT_FAILURE);
    }

    if (1 != EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv)) {
        ERR_print_errors_fp(stderr);
        EVP_CIPHER_CTX_free(ctx);
        free(padded_message);
        exit(EXIT_FAILURE);
    }

    if (1 != EVP_EncryptUpdate(ctx, encrypted, &ciphertext_len, padded_message,
                             plaintext_len)) {
        ERR_print_errors_fp(stderr);
        EVP_CIPHER_CTX_free(ctx);
        free(padded_message);
        exit(EXIT_FAILURE);
    }

    int final_len = 0;
    if (1 != EVP_EncryptFinal_ex(ctx, encrypted + ciphertext_len, &final_len)) {
        ERR_print_errors_fp(stderr);
        EVP_CIPHER_CTX_free(ctx);
        free(padded_message);
        exit(EXIT_FAILURE);
    }
    *len = ciphertext_len + final_len;

    EVP_CIPHER_CTX_free(ctx);
    free(padded_message);
}

void decrypt_message(const unsigned char *key, const unsigned char *iv,
                     const unsigned char *encrypted, unsigned char *decrypted,
                     int *len) {
    EVP_CIPHER_CTX *ctx;
    int plaintext_len = 0;

    if (!(ctx = EVP_CIPHER_CTX_new())) {
        ERR_print_errors_fp(stderr);
        exit(EXIT_FAILURE);
    }

    if (1 != EVP_DecryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv)) {
        ERR_print_errors_fp(stderr);
        EVP_CIPHER_CTX_free(ctx);
        exit(EXIT_FAILURE);
    }

    if (1 != EVP_DecryptUpdate(ctx, decrypted, &plaintext_len, encrypted, *len)) {
        ERR_print_errors_fp(stderr);
        EVP_CIPHER_CTX_free(ctx);
        exit(EXIT_FAILURE);
    }

    int final_len = 0;
    if (1 != EVP_DecryptFinal_ex(ctx, decrypted + plaintext_len, &final_len)) {
        ERR_print_errors_fp(stderr);
        EVP_CIPHER_CTX_free(ctx);
        exit(EXIT_FAILURE);
    }
    *len = plaintext_len + final_len;

    pkcs7_unpad(decrypted, len, BLOCK_SIZE);

    EVP_CIPHER_CTX_free(ctx);
} 