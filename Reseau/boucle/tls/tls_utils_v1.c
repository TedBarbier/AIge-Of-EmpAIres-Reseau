#ifdef _WIN32
#include <windows.h>
#endif

#include "tls_utils_v1.h"
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
    HMAC_CTX *ctx = HMAC_CTX_new();
    unsigned int hmac_len;
    int result = 1;

    if (!ctx) {
        fprintf(stderr, "Error creating HMAC context\n");
        return 0;
    }

    if (!HMAC_Init_ex(ctx, hmac_key, HMAC_KEY_LENGTH, EVP_sha256(), NULL)) {
        fprintf(stderr, "Error initializing HMAC\n");
        result = 0;
        goto cleanup;
    }

    if (!HMAC_Update(ctx, message, message_len)) {
        fprintf(stderr, "Error updating HMAC\n");
        result = 0;
        goto cleanup;
    }

    if (!HMAC_Final(ctx, hmac, &hmac_len)) {
        fprintf(stderr, "Error finalizing HMAC\n");
        result = 0;
        goto cleanup;
    }

    if (hmac_len != HMAC_LENGTH) {
        fprintf(stderr, "Invalid HMAC length: %u (expected %d)\n", hmac_len, HMAC_LENGTH);
        result = 0;
        goto cleanup;
    }

cleanup:
    HMAC_CTX_free(ctx);
    return result;
}

int verify_hmac(const unsigned char *hmac_key, const unsigned char *message,
                int message_len, const unsigned char *received_hmac) {
    unsigned char calculated_hmac[HMAC_LENGTH];
    
    if (!generate_hmac(hmac_key, message, message_len, calculated_hmac)) {
        return 0;
    }
    
    // Comparaison sécurisée contre les attaques temporelles
    int result = 1;
    for (int i = 0; i < HMAC_LENGTH; i++) {
        if (calculated_hmac[i] != received_hmac[i]) {
            result = 0;
            break;
        }
    }
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
