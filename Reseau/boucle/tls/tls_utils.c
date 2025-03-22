#include "tls_utils.h"
#include <openssl/err.h>
#include <openssl/evp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Define key and IV lengths for AES-256-CBC
#define KEY_LENGTH 32
#define IV_LENGTH 16
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

void encrypt_message(const unsigned char *key, const unsigned char *iv,
                     const char *message, unsigned char *encrypted, int *len) {
  EVP_CIPHER_CTX *ctx;
  int ciphertext_len = 0;
  int plaintext_len = strlen(message);
  unsigned char *padded_message = malloc(plaintext_len + BLOCK_SIZE);

  memcpy(padded_message, message, plaintext_len);
  pkcs7_pad(padded_message, &plaintext_len, BLOCK_SIZE);

  /* Create and initialize the context */
  if (!(ctx = EVP_CIPHER_CTX_new())) {
    ERR_print_errors_fp(stderr);
    exit(EXIT_FAILURE);
  }

  /* Initialize the encryption operation */
  if (1 != EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv)) {
    ERR_print_errors_fp(stderr);
    EVP_CIPHER_CTX_free(ctx);
    exit(EXIT_FAILURE);
  }

  /* Provide the message to be encrypted, and obtain the encrypted output */
  if (1 != EVP_EncryptUpdate(ctx, encrypted, &ciphertext_len, padded_message,
                             plaintext_len)) {
    ERR_print_errors_fp(stderr);
    EVP_CIPHER_CTX_free(ctx);
    exit(EXIT_FAILURE);
  }

  /* Finalize the encryption */
  int final_len = 0;
  if (1 != EVP_EncryptFinal_ex(ctx, encrypted + ciphertext_len, &final_len)) {
    ERR_print_errors_fp(stderr);
    EVP_CIPHER_CTX_free(ctx);
    exit(EXIT_FAILURE);
  }
  *len = ciphertext_len + final_len;

  /* Debugging: Print the length of the encrypted data */
  printf("Encrypted length: %d\n", *len);

  /* Debugging: Print the encrypted data */
  printf("Encrypted data: ");
  for (int i = 0; i < *len; i++) {
    printf("%02x", encrypted[i]);
  }
  printf("\n");

  /* Clean up */
  EVP_CIPHER_CTX_free(ctx);
  free(padded_message);
}

void decrypt_message(const unsigned char *key, const unsigned char *iv,
                     const unsigned char *encrypted, unsigned char *decrypted,
                     int *len) {
  EVP_CIPHER_CTX *ctx;
  int plaintext_len = 0;

  /* Create and initialize the context */
  if (!(ctx = EVP_CIPHER_CTX_new())) {
    ERR_print_errors_fp(stderr);
    exit(EXIT_FAILURE);
  }

  /* Initialize the decryption operation */
  if (1 != EVP_DecryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv)) {
    ERR_print_errors_fp(stderr);
    EVP_CIPHER_CTX_free(ctx);
    exit(EXIT_FAILURE);
  }

  /* Provide the encrypted message, and obtain the plaintext output */
  if (1 != EVP_DecryptUpdate(ctx, decrypted, &plaintext_len, encrypted, *len)) {
    ERR_print_errors_fp(stderr);
    EVP_CIPHER_CTX_free(ctx);
    exit(EXIT_FAILURE);
  }

  /* Finalize the decryption */
  int final_len = 0;
  if (1 != EVP_DecryptFinal_ex(ctx, decrypted + plaintext_len, &final_len)) {
    ERR_print_errors_fp(stderr);
    EVP_CIPHER_CTX_free(ctx);
    exit(EXIT_FAILURE);
  }
  *len = plaintext_len + final_len;

  /* Remove padding */
  pkcs7_unpad(decrypted, len, BLOCK_SIZE);

  /* Debugging: Print the length of the decrypted data */
  printf("Decrypted length: %d\n", *len);

  /* Debugging: Print the decrypted data */
  printf("Decrypted data: ");
  for (int i = 0; i < *len; i++) {
    printf("%02x", decrypted[i]);
  }
  printf("\n");

  /* Clean up */
  EVP_CIPHER_CTX_free(ctx);
}
