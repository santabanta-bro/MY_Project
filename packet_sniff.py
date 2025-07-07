import socket
import struct
import argparse
import logging


logging.basicConfig(filename='C:\\Users\\user\\Desktop\\Badfile\\network_capture.log', level=logging.INFO, format='%(asctime)s - %(message)s')


def parse_ip_header(data):
    ip_header = struct.unpack('!BBHHHBBH4s4s', data[:20])
    version_ihl = ip_header[0]
    version = version_ihl >> 4
    ihl = version_ihl & 0xF
    total_length = ip_header[2]
    protocol = ip_header[6]
    src_addr = socket.inet_ntoa(ip_header[8])
    dest_addr = socket.inet_ntoa(ip_header[9])
    return version, ihl, total_length, protocol, src_addr, dest_addr

def parse_tcp_header(data, ihl):
    tcp_header = struct.unpack('!HHLLBBHHH', data[ihl:ihl+20])
    src_port = tcp_header[0]
    dest_port = tcp_header[1]
    data_offset = (tcp_header[4] >> 4) * 4
    payload = data[ihl+data_offset:]
    return src_port, dest_port, payload

def parse_udp_header(data, ihl):
    udp_header = struct.unpack('!HHHH', data[ihl:ihl+8])
    src_port = udp_header[0]
    dest_port = udp_header[1]
    payload = data[ihl+8:]
    return src_port, dest_port, payload

def analyze_packet(packet, filter_protocols):
    version, ihl, total_length, protocol, src_addr, dest_addr = parse_ip_header(packet)
    
    if filter_protocols and protocol not in filter_protocols:
        return

    logging.info(f"Packet: {src_addr} -> {dest_addr}, Protocol: {protocol}, Length: {total_length}")

    if protocol == 6:  # TCP
        src_port, dest_port, payload = parse_tcp_header(packet, ihl * 4)
        logging.info(f"TCP Packet: {src_addr}:{src_port} -> {dest_addr}:{dest_port}, Payload: {len(payload)} bytes")
        if payload:
            logging.info(f"Payload (Hex): {payload.hex()}")
            try:
                logging.info(f"Payload (ASCII): {payload.decode('ascii', errors='ignore')}")
            except Exception as e:
                logging.error(f"Error decoding payload: {e}")

    elif protocol == 17:  # UDP
        src_port, dest_port, payload = parse_udp_header(packet, ihl * 4)
        logging.info(f"UDP Packet: {src_addr}:{src_port} -> {dest_addr}:{dest_port}, Payload: {len(payload)} bytes")
        if payload:
            logging.info(f"Payload (Hex): {payload.hex()}")
            try:
                logging.info(f"Payload (ASCII): {payload.decode('ascii', errors='ignore')}")
            except Exception as e:
                logging.error(f"Error decoding payload: {e}")

def main():
    parser = argparse.ArgumentParser(description="Packet capture utility")
    parser.add_argument('--filter-protocols', type=int, nargs='*', choices=[6, 17], help="Filter packets by protocol (6 for TCP, 17 for UDP)")
    args = parser.parse_args()

    # Create a raw socket and bind it to the public interface
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
    host = socket.gethostbyname(socket.gethostname())
    sock.bind((host, 0))

    # Include IP headers
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

    # Enable promiscuous mode
    sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

    try:
        logging.info("Starting packet capture...")
        while True:
            # Receive packets
            packet, _ = sock.recvfrom(65565)
            analyze_packet(packet, filter_protocols=args.filter_protocols)

    except KeyboardInterrupt:
        # Disable promiscuous mode
        sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
        logging.info("Stopped packet capture.")

if __name__ == "__main__":
    main()
