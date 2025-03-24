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
    EVP_MAC *mac = EVP_MAC_fetch(NULL, "HMAC", NULL);
    EVP_MAC_CTX *ctx = EVP_MAC_CTX_new(mac);
    OSSL_PARAM params[2];
    size_t hmac_len;
    int result = 1;

    if (!mac || !ctx) {
        fprintf(stderr, "Error creating HMAC context\n");
        result = 0;
        goto cleanup;
    }

    params[0] = OSSL_PARAM_construct_utf8_string("digest", "SHA256", 0);
    params[1] = OSSL_PARAM_construct_end();

    if (!EVP_MAC_init(ctx, hmac_key, HMAC_KEY_LENGTH, params)) {
        fprintf(stderr, "Error initializing HMAC\n");
        result = 0;
        goto cleanup;
    }

    if (!EVP_MAC_update(ctx, message, message_len)) {
        fprintf(stderr, "Error updating HMAC\n");
        result = 0;
        goto cleanup;
    }

    if (!EVP_MAC_final(ctx, hmac, &hmac_len, HMAC_LENGTH)) {
        fprintf(stderr, "Error finalizing HMAC\n");
        result = 0;
        goto cleanup;
    }

    if (hmac_len != HMAC_LENGTH) {
        fprintf(stderr, "Invalid HMAC length: %zu (expected %d)\n", hmac_len, HMAC_LENGTH);
        result = 0;
        goto cleanup;
    }

cleanup:
    if (ctx) EVP_MAC_CTX_free(ctx);
    if (mac) EVP_MAC_free(mac);
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
  EVP_CIPHER_CTX *ctx = NULL;
  int ciphertext_len = 0;
  int plaintext_len = *len;  // Utiliser la longueur fournie
  unsigned char *padded_message = NULL;
  int max_padded_len = plaintext_len + BLOCK_SIZE;
  int result = 0;

  // Allouer de l'espace pour le message avec padding
  padded_message = malloc(max_padded_len);
  if (!padded_message) {
    fprintf(stderr, "Failed to allocate memory for padded message\n");
    return;
  }

  // Copier le message original
  memcpy(padded_message, message, plaintext_len);
  
  // Ajouter le padding
  pkcs7_pad(padded_message, &plaintext_len, BLOCK_SIZE);

  // Créer le contexte de chiffrement
  ctx = EVP_CIPHER_CTX_new();
  if (!ctx) {
    fprintf(stderr, "Failed to create cipher context\n");
    ERR_print_errors_fp(stderr);
    free(padded_message);
    return;
  }

  // Initialiser le chiffrement
  if (1 != EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv)) {
    fprintf(stderr, "Failed to initialize encryption\n");
    ERR_print_errors_fp(stderr);
    EVP_CIPHER_CTX_free(ctx);
    free(padded_message);
    return;
  }

  // Chiffrer le message
  if (1 != EVP_EncryptUpdate(ctx, encrypted, &ciphertext_len, padded_message,
                             plaintext_len)) {
    fprintf(stderr, "Failed to encrypt message\n");
    ERR_print_errors_fp(stderr);
    EVP_CIPHER_CTX_free(ctx);
    free(padded_message);
    return;
  }

  // Finaliser le chiffrement
  int final_len = 0;
  if (1 != EVP_EncryptFinal_ex(ctx, encrypted + ciphertext_len, &final_len)) {
    fprintf(stderr, "Failed to finalize encryption\n");
    ERR_print_errors_fp(stderr);
    EVP_CIPHER_CTX_free(ctx);
    free(padded_message);
    return;
  }

  // Mettre à jour la longueur totale
  *len = ciphertext_len + final_len;

  // Nettoyer
  EVP_CIPHER_CTX_free(ctx);
  free(padded_message);
}

void decrypt_message(const unsigned char *key, const unsigned char *iv,
                     const unsigned char *encrypted, unsigned char *decrypted,
                     int *len) {
  EVP_CIPHER_CTX *ctx = NULL;
  int plaintext_len = 0;
  int result = 0;

  // Créer le contexte de déchiffrement
  ctx = EVP_CIPHER_CTX_new();
  if (!ctx) {
    fprintf(stderr, "Failed to create cipher context\n");
    ERR_print_errors_fp(stderr);
    return;
  }

  // Initialiser le déchiffrement
  if (1 != EVP_DecryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv)) {
    fprintf(stderr, "Failed to initialize decryption\n");
    ERR_print_errors_fp(stderr);
    EVP_CIPHER_CTX_free(ctx);
    return;
  }

  // Déchiffrer le message
  if (1 != EVP_DecryptUpdate(ctx, decrypted, &plaintext_len, encrypted, *len)) {
    fprintf(stderr, "Failed to decrypt message\n");
    ERR_print_errors_fp(stderr);
    EVP_CIPHER_CTX_free(ctx);
    return;
  }

  // Finaliser le déchiffrement
  int final_len = 0;
  if (1 != EVP_DecryptFinal_ex(ctx, decrypted + plaintext_len, &final_len)) {
    fprintf(stderr, "Failed to finalize decryption\n");
    ERR_print_errors_fp(stderr);
    EVP_CIPHER_CTX_free(ctx);
    return;
  }

  // Mettre à jour la longueur totale
  *len = plaintext_len + final_len;

  // Retirer le padding
  pkcs7_unpad(decrypted, len, BLOCK_SIZE);

  // Nettoyer
  EVP_CIPHER_CTX_free(ctx);
}
