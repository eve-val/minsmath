import urllib2
from xml.etree import ElementTree

def get_buys(item_id,region):
    try:
        response = urllib2.urlopen("http://api.eve-central.com/api/quicklook?typeid="+str(item_id)+"&regionlimit="+str(region))
        tree = ElementTree.parse(response)
        ql = tree.find('quicklook')
        if ql == None:
            return -1
        buy_orders = ql.find('buy_orders')
    except urllib2.HTTPError:
        return(-1)
    return(buy_orders)

def get_sys_buys(item_id,system):
    try:
        response = urllib2.urlopen("http://api.eve-central.com/api/quicklook?typeid="+str(item_id)+"&usesystem="+str(system))
        tree = ElementTree.parse(response)
        ql = tree.find('quicklook')
        if ql == None:
            return -1
        buy_orders = ql.find('buy_orders')
    except urllib2.HTTPError:
        return(-1)
    return(buy_orders)


def find_sys_price(item_id,system):
    buy_orders = get_sys_buys(item_id,system)
    if buy_orders == -1:
        return 0
    best = 0
    for order in buy_orders:
       if float(order.find('price').text) > best:
            best = float(order.find('price').text) 
    return best

def find_best_price(item_id,region):
    buy_orders = get_buys(item_id,region)
    if buy_orders == -1:
        return 0
    best = 0
    for order in buy_orders:
       if float(order.find('price').text) > best:
            best = float(order.find('price').text) 
    return best
