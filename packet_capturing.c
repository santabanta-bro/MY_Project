#include <pcap.h>
#include <stdio.h>
#include <arpa/inet.h>

void packet_handler(u_char *param, const struct pcap_pkthdr *header, const u_char *pkt_data) {
    printf("Packet captured length: %d\n", header->len);
}

int main() {
    char *dev;
    char errbuf[PCAP_ERRBUF_SIZE];
    pcap_t *handle;

    // Find a network device
    dev = pcap_lookupdev(errbuf);
    if (dev == NULL) {
        printf("Error finding device: %s\n", errbuf);
        return 1;
    }
    printf("Using device: %s\n", dev);

    // Open the device for capturing
    handle = pcap_open_live(dev, BUFSIZ, 1, 1000, errbuf);
    if (handle == NULL) {
        printf("Error opening device: %s\n", errbuf);
        return 1;
    }

    // Capture packets
    pcap_loop(handle, 0, packet_handler, NULL);

    // Close the handle
    pcap_close(handle);
    return 0;
}
