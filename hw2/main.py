import socket
import time
import matplotlib.pyplot as plt
import random

# 模拟丢包的函数，模拟网络中的不稳定情况
def unreliable_send(sock, data, addr, loss_prob=0.1):
    if random.random() > loss_prob:
        sock.sendto(data, addr)

# Stop-and-Wait 协议的客户端实现
class StopAndWaitClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.delays = []
        self.timeout_interval = 0.1  # 超时时间设为0.1秒

    def send_message(self, message, num_packets):
        seq_num = 0

        for pkt_num in range(num_packets):
            ack_received = False
            start_time = time.time()  # 初次发送时间
            while not ack_received:
                # 发送数据包
                packet = f"{seq_num}:{message} {pkt_num}".encode()
                unreliable_send(self.sock, packet, (self.server_ip, self.server_port))
                print(f"客户端: 已发送数据包: {packet.decode()}")
                
                # 设置定时器并检测超时
                send_time = time.time()
                while True:
                    # 计算当前延迟
                    delay = time.time() - send_time

                    # 超时重发逻辑
                    if delay > self.timeout_interval:
                        print("客户端: ACK 超时，重发数据包...")
                        break  # 跳出内部循环，重发数据包

                    # 设置非阻塞模式并尝试接收ACK
                    self.sock.setblocking(False)
                    try:
                        ack, _ = self.sock.recvfrom(1024)
                        ack = ack.decode()
                        if ack == f"ACK{seq_num}":
                            # 收到正确的ACK
                            total_delay = time.time() - start_time
                            self.delays.append(total_delay)
                            print(f"客户端: 收到 ACK: {ack}, 延时: {total_delay * 1000:.2f} 毫秒")
                            ack_received = True
                            break
                        else:
                            print(f"客户端: 收到错误的 ACK: {ack}")
                    except BlockingIOError:
                        # 没有数据收到，继续等待直到超时
                        time.sleep(0.01)
        
            # 切换序列号
            seq_num = 1 - seq_num

    def close(self):
        self.sock.close()
        # 绘制包延时图
        plt.plot(self.delays, marker='o')
        plt.xlabel('Packet Number')
        plt.ylabel('Delay (seconds)')
        plt.title('Stop-and-Wait Protocol Packet Delays')
        plt.grid()
        plt.savefig('stop_and_wait_delays.png')
        plt.show()

# Stop-and-Wait 协议的服务器实现
class StopAndWaitServer:
    def __init__(self, port):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", self.port))
        self.expected_seq_num = 0

    def start(self):
        print("服务器: 等待客户端连接...")
        while True:
            try:
                # 接收数据包
                data, client_addr = self.sock.recvfrom(1024)
                data = data.decode()
                seq_num, message = data.split(":", 1)
                seq_num = int(seq_num)
                print(f"服务器: 收到数据包: {data}")

                # 检查序列号是否匹配
                if seq_num == self.expected_seq_num:
                    print(f"服务器: 数据包正确，内容: {message}")
                    # 发送 ACK
                    ack = f"ACK{seq_num}".encode()
                    self.sock.sendto(ack, client_addr)
                    print(f"服务器: 已发送 ACK: {ack.decode()}")
                    # 切换期待的序列号
                    self.expected_seq_num = 1 - self.expected_seq_num
                else:
                    # 发送上一个 ACK 以通知丢包
                    ack = f"ACK{1 - self.expected_seq_num}".encode()
                    self.sock.sendto(ack, client_addr)
                    print(f"服务器: 收到错误的序列号，重发 ACK: {ack.decode()}")
            except Exception as e:
                print(f"服务器: 发生错误: {e}")

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
