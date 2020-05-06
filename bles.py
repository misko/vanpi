from bluepy.btle import Scanner, DefaultDelegate

known_bles={
    'c1:ec:7b:ca:46:2b':'car_keys',
    'cb:65:67:9a:fe:65':'bubs',
    'e2:4e:71:ce:bd:00':'daisy'
    }

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        return


def scan():
    scanner = Scanner().withDelegate(ScanDelegate())
    devices = scanner.scan(10.0)
    keys = list(known_bles.keys())
    keys.sort()
    addrs_found = {} 
    for dev in devices:
        addrs_found[dev.addr]=dev
    whos_here = []
    for key in keys:
        if key in addrs_found:
            # thing is here
            whos_here.append( (known_bles[key], addrs_found[key].rssi)) 
        else:
            #thing is not here
            whos_here.append( (known_bles[key], -1000))
    return whos_here

