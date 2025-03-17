import socket
import struct
import time

def send_test_data():
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        # Test data that matches the C GameState structure
        test_data = struct.pack(
            '=i 4i f 5H B',        # Format string matching C structure
            100,                    # villager_count
            1000,                   # wood
            800,                    # food
            600,                    # stone
            400,                    # gold
            0.75,                   # military_ratio
            5,                      # storage_count
            3,                      # training_count
            10,                     # military_free
            50,                     # villager_total
            20,                     # villager_free
            1                       # housing_crisis
        )
        
        # First send the size of the data
        data_size = struct.pack('!I', len(test_data))
        sock.sendto(data_size, ('localhost', 12345))
        
        # Then send the actual data
        sock.sendto(test_data, ('localhost', 12345))
        print("Data sent successfully")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    while True:
        send_test_data()
        time.sleep(2)  # Send every 2 seconds