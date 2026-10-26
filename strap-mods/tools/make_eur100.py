"""Build an override of the vanilla MI_MoneyPack_EUR100 (green strap) from the mod's MI_MoneyPack_EUR200,
which is a renamed clone of it (same size, same layout)."""
import struct, sys, re
import cityhash as C

def rebuild(src, strap_srgb_hex):
    d=bytearray(src)
    def nmhash(s): return C.cityhash64(s.lower().encode('ascii'))
    def exphash(s): return C.cityhash64(s.lower().encode('utf-16le'))
    def rename(s):
        assert s.count('200')==1 or s.count('200')==0
        return s.replace('200','100')
    def fix_namemap(off):
        n,blob,hv=struct.unpack_from('<IIQ',d,off); o=off+16
        hs=o; o+=8*n
        lens=[struct.unpack_from('>H',d,o+2*k)[0] for k in range(n)]; lo=o; o+=2*n
        names=[]
        for k,L in enumerate(lens):
            s=bytes(d[o:o+L]).decode('ascii')
            ns=rename(s)
            if ns!=s:
                assert len(ns)==len(s)
                d[o:o+L]=ns.encode('ascii')
                struct.pack_into('<Q',d,hs+8*k,nmhash(ns))
            names.append(ns); o+=L
        # sanity: every hash now valid
        for k,s in enumerate(names):
            assert struct.unpack_from('<Q',d,hs+8*k)[0]==nmhash(s),(k,s)
        return names,o
    f=struct.unpack_from('<13I',d,0)
    names,end=fix_namemap(52)
    inames,end2=fix_namemap(f[12]+0)  # imported package names (same name-map serialisation, count then blob...)
    # imported public export hashes: [MI_MoneyPack, T_moneyEURO200, T_moneyEuro200_FactoryMark]
    ip=f[6]
    new_imp=[exphash('MI_MoneyPack'),exphash('T_moneyEURO100'),exphash('T_moneyEuro100_FactoryMark')]
    old=struct.unpack_from('<3Q',d,ip)
    assert old[0]==new_imp[0] and old[1]==exphash('T_moneyEURO200') and old[2]==exphash('T_moneyEuro200_FactoryMark'),'unexpected import hashes'
    struct.pack_into('<3Q',d,ip,*new_imp)
    # export public hash
    ex=f[8]
    assert struct.unpack_from('<Q',d,ex+56)[0]==exphash('MI_MoneyPack_EUR200')
    struct.pack_into('<Q',d,ex+56,exphash('MI_MoneyPack_EUR100'))
    # strap colour (TapeColorB), located relative to TapeColorA
    pos_a=None
    for o in range(len(d)-16):
        a=struct.unpack_from('<4f',d,o)
        if abs(a[0]-0.9219)<1e-3 and abs(a[1]-0.8445)<1e-3 and abs(a[2]-0.4993)<1e-3 and a[3]==1.0: pos_a=o;break
    assert pos_a
    pb=pos_a+49
    oldb=struct.unpack_from('<4f',d,pb); assert oldb[3]==1.0
    if isinstance(strap_srgb_hex,(tuple,list)):
        lin=list(strap_srgb_hex)   # exact linear RGB
    else:
        v=strap_srgb_hex.lstrip('#')
        lin=[(c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4) for c in (int(v[i:i+2],16)/255 for i in (0,2,4))]
    struct.pack_into('<3f',d,pb,*lin)
    return bytes(d), names, inames, oldb[:3], lin

if __name__=='__main__':
    pass
