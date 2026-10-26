"""Standalone IoStore container with N assets in one directory; every block 16-byte aligned, file padded."""
import struct
import cityhash as C, iobuild as B

def dir_index_multi(dir_chain, fnames):
    strs=list(dir_chain)+list(fnames)
    nd=len(dir_chain)
    ents=[(0xFFFFFFFF,1 if nd else 0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF)]
    for k in range(nd):
        last=(k==nd-1)
        ents.append((k,0xFFFFFFFF if last else k+2,0xFFFFFFFF,0 if last else 0xFFFFFFFF))
    out=B.fstr('../../../')+struct.pack('<I',len(ents))+b''.join(struct.pack('<4I',*e) for e in ents)
    nf=len(fnames)
    out+=struct.pack('<I',nf)
    for k in range(nf):
        out+=struct.pack('<3I',nd+k,k+1 if k<nf-1 else 0xFFFFFFFF,k)
    out+=struct.pack('<I',len(strs))+b''.join(B.fstr(s) for s in strs)
    return out

def build_container(container_name, dir_chain, assets):
    """assets: list of (file_name, package_id, asset_bytes, imported_package_ids). Returns (utoc, ucas)."""
    cid=C.pkgid(container_name)
    hdr=B.container_header(cid,[(pid,imps) for _,pid,_,imps in assets])
    chunks=[(B.chunk_id(pid,1),data) for _,pid,data,_ in assets]+[(B.chunk_id(cid,6),hdr)]
    n=len(chunks)
    ucas=b''; blocks=b''; offs=b''
    for k,(_,data) in enumerate(chunks):
        ucas+=b'\0'*((-len(ucas))%16)
        pos=len(ucas)
        blocks+=pos.to_bytes(5,'little')+len(data).to_bytes(3,'little')+len(data).to_bytes(3,'little')+b'\0'
        offs+=(k*65536).to_bytes(5,'big')+len(data).to_bytes(5,'big')
        ucas+=data
    ucas+=b'\0'*((-len(ucas))%16)
    di=dir_index_multi(dir_chain,[a[0] for a in assets])
    h=b'-==--==--==--==-'+struct.pack('<B3x',6)+struct.pack('<9I',144,n,n,12,0,32,65536,len(di),1)
    h+=struct.pack('<Q',cid)+b'\0'*16+struct.pack('<B3x',8)+struct.pack('<I',0)+struct.pack('<Q',0xFFFFFFFFFFFFFFFF)+struct.pack('<I',0)
    h=h.ljust(144,b'\0')
    toc=h+b''.join(c[0] for c in chunks)+offs+blocks+di+b'\0'*(33*n)
    return toc,ucas
