"""Minimal single-asset IoStore container writer (uncompressed, UE5 toc v6, no perfect hash)."""
import struct
import cityhash as C

def fstr(s):
    b=s.encode('ascii')+b'\0'
    return struct.pack('<i',len(b))+b

def dir_index(asset_path):
    """asset_path like 'CashCleanerSimulator/Content/Art/Money/X.uasset' ; one file, chain of dirs."""
    parts=asset_path.split('/'); dirs=parts[:-1]; fname=parts[-1]
    strs=dirs+[fname]
    # dir entries: root + one per dir
    ents=[(0xFFFFFFFF,1 if dirs else 0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF)]
    for k,_ in enumerate(dirs):
        last=(k==len(dirs)-1)
        ents.append((k,0xFFFFFFFF if last else k+2,0xFFFFFFFF,0 if last else 0xFFFFFFFF))
    out=fstr('../../../')
    out+=struct.pack('<I',len(ents))+b''.join(struct.pack('<4I',*e) for e in ents)
    out+=struct.pack('<I',1)+struct.pack('<3I',len(dirs),0xFFFFFFFF,0)
    out+=struct.pack('<I',len(strs))+b''.join(fstr(s) for s in strs)
    return out

def build_toc(container_id, chunks, asset_path):
    """chunks: list of (chunk_id_12bytes, virtual_offset, length). Blocks packed back-to-back."""
    n=len(chunks)
    hdr=b'-==--==--==--==-'+struct.pack('<B3x',6)
    di=dir_index(asset_path)
    hdr+=struct.pack('<9I',144,n,n,12,0,32,65536,len(di),1)
    hdr+=struct.pack('<Q',container_id)+b'\0'*16+struct.pack('<B3x',8)
    hdr+=struct.pack('<I',0)+struct.pack('<Q',0xFFFFFFFFFFFFFFFF)+struct.pack('<I',0)
    hdr=hdr.ljust(144,b'\0'); assert len(hdr)==144
    body=b''.join(c[0] for c in chunks)
    body+=b''.join(c[1].to_bytes(5,'big')+c[2].to_bytes(5,'big') for c in chunks)
    pos=0; blocks=b''
    for _,_,ln in chunks:
        blocks+=pos.to_bytes(5,'little')+ln.to_bytes(3,'little')+ln.to_bytes(3,'little')+b'\0'; pos+=ln
    body+=blocks+di+b'\0'*(33*n)
    return hdr+body

def chunk_id(pkg_id,typ,index=0): return struct.pack('<QHBB',pkg_id,index,0,typ)

def container_header(container_id,pkgs):
    """pkgs: list of (package_id, [imported package ids])"""
    out=struct.pack('<IIQI',0x496f436e,3,container_id,len(pkgs))
    out+=b''.join(struct.pack('<Q',p) for p,_ in pkgs)
    hdrs=b'';data=b''
    base=16*len(pkgs)
    for k,(_,imps) in enumerate(pkgs):
        field_pos=k*16
        off=base+len(data)-field_pos
        hdrs+=struct.pack('<II',len(imps),off if imps else 0)+struct.pack('<II',0,0)
        data+=b''.join(struct.pack('<Q',i) for i in imps)
    se=hdrs+data
    out+=struct.pack('<I',len(se))+se
    out+=b'\0'*32
    return out
