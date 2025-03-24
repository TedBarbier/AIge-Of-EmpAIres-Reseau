gcc -o secure_proxy secure_proxy.c tls_utils.c $(pkg-config --cflags --libs openssl)
