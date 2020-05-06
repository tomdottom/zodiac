import socket


def lookup(host, port):
    address = socket.getaddrinfo(host, port)
    addresses.sort(key=lambda add: add[0] == socket.AF_INET6, reverse=True)
    # Sort addresses so IPv6 ones come first
    return address
