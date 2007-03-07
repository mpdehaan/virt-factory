#!/usr/bin/python


#
# Copyright (c) 1999-2007 Red Hat, Inc.  Distributed under GPL.
#
# Author: Preston Brown <pbrown@redhat.com>
#         Adrian Likins <alikins@redhat.com>
#         Cristian Gafton <gafton@redhat.com>
#


# All of this is heavily based on code from hardware.py in up2date
import socket
import string

from rhpl import ethtool

def findHostByRoute(server_url, proxy_url=None):

    # up2date supports multiple serverUrls, probably not needed here -akl
    sl = [server_url]
    st = {'https':443, 'http':80}

    hostname = None
    intf = None
    for serverUrl in sl:
        s = socket.socket()
        server = string.split(serverUrl, '/')[2]
        servertype = string.split(serverUrl, ':')[0]
        port = st[servertype]

        if proxy_url:
            server_port = getProxySetting(proxy_url)
            (server, port) = string.split(server_port, ':')
            port = int(port)

        try:
            # RHEL3 doesn't let you set a timeout, see #164660
            if hasattr(s, "settimeout"):
                s.settimeout(5)
            s.connect((server, port))
            (intf, port) = s.getsockname()
            hostname = socket.gethostbyaddr(intf)[0]
        # I dislike generic excepts, but is the above fails
        # for any reason, were not going to be able to
        # find a good hostname....
        except:
            s.close()
            continue
    if hostname == None:
        hostname = "unknown"
        s.close()
    return hostname, intf


def get_netinfo(server_url, proxy_url=None):
    machine_data = read_network(server_url, proxy_url)
    net_interfaces = read_network_interfaces()

    ip_addr = machine_data['ipaddr']
    hwaddr = get_hwaddr_for_route(ip_addr, net_interfaces)

    return {'ipaddr': ip_addr, 'hwaddr':hwaddr, 'hostname': machine_data['hostname']}

def get_hwaddr_for_route(ip_addr, net_interfaces):
    for intf in net_interfaces.keys():
        if intf == "class":
            # uh, read data struct there...
            continue
        intf_data = net_interfaces[intf]
        if intf_data['ipaddr'] == ip_addr:
            return intf_data['hwaddr']
    # hmm, what should we do here...
    return None

def read_network(server_url, proxy_url=None):
    netdict = {}
    netdict['class'] = "NETINFO"

    netdict['hostname'] = socket.gethostname()
    try:
        netdict['ipaddr'] = socket.gethostbyname(socket.gethostname())
    except:
        netdict['ipaddr'] = "127.0.0.1"


    if netdict['hostname'] == 'localhost.localdomain' or \
    netdict['ipaddr'] == "127.0.0.1":
        hostname, ipaddr = findHostByRoute(server_url, proxy_url)
        netdict['hostname'] = hostname
        netdict['ipaddr'] = ipaddr

    return netdict


def getProxySetting(proxy_url):
    proxy = None
    proxyHost = proxy_url

    if proxyHost:
        if proxyHost[:7] == "http://":
            proxy = proxyHost[7:]
        else:
            proxy = proxyHost

    return proxy 

def read_network_interfaces():
    intDict = {}
    intDict['class'] = "NETINTERFACES"

    interfaces = ethtool.get_devices()
    for interface in interfaces:
        try:
            hwaddr = ethtool.get_hwaddr(interface)
        except:
            hwaddr = ""

        try:
            module = ethtool.get_module(interface)
        except:
            if interface == 'lo':
                module = "loopback"
            else:
                module = "Unknown"
        try:
            ipaddr = ethtool.get_ipaddr(interface)
        except:
            ipaddr = ""

        try:
            netmask = ethtool.get_netmask(interface)
        except:
            netmask = ""

        try:
            broadcast = ethtool.get_broadcast(interface)
        except:
            broadcast = ""

        intDict[interface] = {'hwaddr':hwaddr,
                              'ipaddr':ipaddr,
                              'netmask':netmask,
                              'broadcast':broadcast,
                              'module': module}

    return intDict
