import struct,sys
import cityhash as C
def namemap_names(d,o):
    n,blob,hv=struct.unpack_from('<IIQ',d,o); o+=16+8*n
    lens=[struct.unpack_from('>H',d,o+2*k)[0] for k in range(n)]; o+=2*n
    out=[]
    for L in lens: out.append(d[o:o+L].decode('ascii')); o+=L
    return out
def tape_b_offset(d):
    for o in range(len(d)-16):
        x=struct.unpack_from('<4f',d,o)
        if abs(x[0]-0.9219)<1e-3 and abs(x[1]-0.8445)<1e-3 and abs(x[2]-0.4993)<1e-3 and x[3]==1.0: return o+49
    raise ValueError('TapeColorA not found')
def imports_of(d):
    f=struct.unpack_from('<13I',d,0)
    return [C.pkgid(n) for n in namemap_names(d,f[12])]
