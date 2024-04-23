import socket
import codecs
import time
import os
from random import randbytes

from struct import unpack
from socket import inet_ntoa

from threading import Thread

import bencoder

PER_NID_LEN = 20
buff = 65535
SLEEP_TIME = 1e-5

MAGNET_PER = "magnet:?xt=urn:btih:{}"

PER_NODE_LEN = 26
PER_NID_NIP_LEN = 24
NEIGHBOR_END = 14

nid = randbytes(20)

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
udp.bind(("0.0.0.0", 9090))


def new_node():
    msg = {b"t": os.urandom(3), b"y": "q", b"q": "ping", b"a": {b"id": nid}}
    udp.sendto(bencoder.encode(msg), ("router.bittorrent.com", 6881))
    udp.sendto(bencoder.encode(msg), ("dht.transmissionbt.com", 6881))
    udp.sendto(bencoder.encode(msg), ("router.utorrent.com", 6881))


def get_nodes_info(nodes):
    nodes_list = []
    length = len(nodes)
    if (length % PER_NODE_LEN) != 0:
        return []
    for i in range(0, length, PER_NODE_LEN):
        nid = nodes[i: i + PER_NID_LEN]
        ip = inet_ntoa(nodes[i + PER_NID_LEN: i + PER_NID_NIP_LEN])
        port = unpack("!H", nodes[i + PER_NID_NIP_LEN: i + PER_NODE_LEN])[0]
        nodes_list.append((nid, ip, port))
    return nodes_list


def get_info_hash(hash_list):
    try:
        for i in range(0, len(hash_list), 20):
            magnet = MAGNET_PER.format(codecs.getencoder("hex")(hash_list[i-20:i])[0].decode())
            print(magnet)
    except Exception as ex:
        print('ex  ' + str(ex))


def sample_info_hashes(ip, port):
    try:
        msg = {b"t": os.urandom(5), b"y": "q", b"q": "sample_infohashes", b"a": {b"id": nid, b"target": os.urandom(20)}}
        udp.sendto(bencoder.encode(msg), (ip, port))
    except Exception as es:
        print('es  ' + str(es))


def find_node():
    msg = {b"t": os.urandom(5), b"y": "q", b"q": "find_node", b"a": {b"id": nid, b"target": os.urandom(20)}}
    udp.sendto(bencoder.encode(msg), ("router.bittorrent.com", 6881))


def get_msg(msg):
    try:
        if msg[b"y"] == b"r":
            if msg[b"r"].get(b"samples"):
                get_info_hash(msg[b"r"].get(b"samples"))
            elif msg[b"r"].get(b"nodes"):
                for node in get_nodes_info(msg[b"r"][b"nodes"]):
                    sample_info_hashes(node[1], node[2])
            else:
                find_node()
        else:
            new_node()
    except Exception as em:
        print('em ' + str(em))


new_node()
while True:
    try:
        data, address = udp.recvfrom(buff)
        msg = bencoder.decode(data)
        time.sleep(SLEEP_TIME)
        thread3 = Thread(target=get_msg, args=(msg,))
        thread3.start()
    except Exception as ee:
        print("ee " + str(ee))
