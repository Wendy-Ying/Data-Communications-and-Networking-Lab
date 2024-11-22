import socket
import time
import matplotlib.pyplot as plt

# 模拟丢包的函数，模拟网络中的不稳定情况
import random
def unreliable_send(sock, data, addr, loss_prob=0.6):
    if random.random() > loss_prob:
        sock.sendto(data, addr)

# Stop-and-Wait 协议的客户端实现
class StopAndWaitClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(0.1)  # 设置超时时间为2秒
        self.delays = []

    def send_message(self, message, num_packets):
        seq_num = 0

        for pkt_num in range(num_packets):
            ack_received = False
            start_time = time.time()

            while not ack_received:
                # Send packet
                packet = f"{seq_num}:{message} {pkt_num}".encode()
                unreliable_send(self.sock, packet, (self.server_ip, self.server_port))
                print(f"Client: Sent packet: {packet.decode()}")

                # Custom timer
                wait_time = 0
                timeout = 1  # 1 second timeout
                while wait_time < timeout and not ack_received:
                    try:
                        self.sock.setblocking(0)  # Set socket to non-blocking mode
                        ack, _ = self.sock.recvfrom(1024)
                        ack = ack.decode()
                        if ack == f"ACK{seq_num}":
                            end_time = time.time()
                            delay = end_time - start_time
                            self.delays.append(delay)
                            print(f"Client: Received ACK: {ack}, Delay: {delay:.2f} seconds")
                            ack_received = True
                        else:
                            print(f"Client: Received incorrect ACK: {ack}")
                    except BlockingIOError:
                        # No data received, wait a bit and retry
                        time.sleep(0.1)  # Wait for a short while
                        wait_time += 0.1

                if not ack_received:
                    print("Client: ACK timeout, resending packet...")

            # Switch sequence number
            seq_num = 1 - seq_num

    def close(self):
        self.sock.close()
        # Plotting the delays
        plt.plot(self.delays, marker='o')
        plt.xlabel('Packet Number')
        plt.ylabel('Delay (seconds)')
        plt.title('Stop-and-Wait Protocol Packet Delays')
        plt.grid()
        plt.savefig('stop_and_wait_delays_origin.png')
        plt.show()

# Stop-and-Wait 协议的服务器实现
class StopAndWaitServer:
    def __init__(self, port):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", self.port))
        self.expected_seq_num = 0

    def start(self):
        print("Server: Waiting for client...")
        while True:
            try:
                # 接收数据包
                data, client_addr = self.sock.recvfrom(1024)
                data = data.decode()
                seq_num, message = data.split(":", 1)
                seq_num = int(seq_num)
                print(f"Server: Receiving packet: {data}")

                # 检查序列号是否匹配
                if seq_num == self.expected_seq_num:
                    print(f"Server: Packet correct, content: {message}")
                    # 发送 ACK
                    ack = f"ACK{seq_num}".encode()
                    self.sock.sendto(ack, client_addr)
                    print(f"Server: Sent ACK: {ack.decode()}")
                    # 切换期待的序列号
                    self.expected_seq_num = 1 - self.expected_seq_num
                else:
                    # 发送上一个 ACK 以通知丢包
                    ack = f"ACK{1 - self.expected_seq_num}".encode()
                    self.sock.sendto(ack, client_addr)
                    print(f"Server: Received incorrect sequence number, resent ACK: {ack.decode()}")
            except Exception as e:
                print(f"Server: Error occurred: {e}")

    def close(self):
        self.sock.close()

# 测试客户端和服务器
if __name__ == "__main__":
    import threading

    # 启动服务器
    server = StopAndWaitServer(port=12345)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()

    # 启动客户端并发送消息
    client = StopAndWaitClient(server_ip="127.0.0.1", server_port=12345)
    time.sleep(1)  # 等待服务器启动

    client.send_message("Hello, Server!", num_packets=50)

    client.close()
    server.close()