import struct
M=(1<<64)-1
k0=0xc3a5c85c97cb3127;k1=0xb492b66fbe98f273;k2=0x9ae16a3b2f90404f;kMul=0x9ddfea08eb382d69
def f64(s,o=0): return struct.unpack_from('<Q',s,o)[0]
def f32(s,o=0): return struct.unpack_from('<I',s,o)[0]
def rot(v,s): return v if s==0 else ((v>>s)|(v<<(64-s)))&M
def sm(v): return v^(v>>47)
def bswap(v): return struct.unpack('>Q',struct.pack('<Q',v))[0]
def h16(u,v,mul=kMul):
    a=((u^v)*mul)&M; a^=a>>47
    b=((v^a)*mul)&M; b^=b>>47
    return (b*mul)&M
def h0_16(s):
    n=len(s)
    if n>=8:
        mul=(k2+n*2)&M; a=(f64(s)+k2)&M; b=f64(s,n-8)
        c=(rot(b,37)*mul+a)&M; d=((rot(a,25)+b)*mul)&M
        return h16(c,d,mul)
    if n>=4:
        mul=(k2+n*2)&M; a=f32(s)
        return h16((n+(a<<3))&M,f32(s,n-4),mul)
    if n>0:
        a=s[0];b=s[n>>1];c=s[n-1]; y=(a+(b<<8))&0xffffffff; z=(n+(c<<2))&0xffffffff
        return (sm(((y*k2)&M)^((z*k0)&M))*k2)&M
    return k2
def h17_32(s):
    n=len(s);mul=(k2+n*2)&M
    a=(f64(s)*k1)&M;b=f64(s,8);c=(f64(s,n-8)*mul)&M;d=(f64(s,n-16)*k2)&M
    return h16((rot((a+b)&M,43)+rot(c,30)+d)&M,(a+rot((b+k2)&M,18)+c)&M,mul)
def weak(w,x,y,z,a,b):
    a=(a+w)&M;b=rot((b+a+z)&M,21);c=a;a=(a+x)&M;a=(a+y)&M;b=(b+rot(a,44))&M
    return ((a+z)&M,(b+c)&M)
def weaks(s,o,a,b): return weak(f64(s,o),f64(s,o+8),f64(s,o+16),f64(s,o+24),a,b)
def h33_64(s):
    n=len(s);mul=(k2+n*2)&M
    a=(f64(s)*k2)&M;b=f64(s,8);c=f64(s,n-24);d=f64(s,n-32);e=(f64(s,16)*k2)&M;f=(f64(s,24)*9)&M;g=f64(s,n-8);h=(f64(s,n-16)*mul)&M
    u=(rot((a+g)&M,43)+(rot(b,30)+c)*9)&M; v=((((a+g)&M)^d)+f+1)&M
    w=(bswap(((u+v)*mul)&M)+h)&M; x=(rot((e+f)&M,42)+c)&M
    y=((bswap(((v+w)*mul)&M)+g)*mul)&M; z=(e+f+c)&M
    a=(bswap(((((x+z)*mul)&M)+y)&M)+b)&M
    b=(sm(((((z+a)*mul)&M)+d+h)&M)*mul)&M
    return (b+x)&M
def cityhash64(s):
    n=len(s)
    if n<=32: return h0_16(s) if n<=16 else h17_32(s)
    if n<=64: return h33_64(s)
    x=f64(s,n-40);y=(f64(s,n-16)+f64(s,n-56))&M;z=h16((f64(s,n-48)+n)&M,f64(s,n-24))
    v=weaks(s,n-64,n,z);w=weaks(s,n-32,(y+k1)&M,x);x=(x*k1+f64(s))&M
    n=(n-1)&~63;o=0
    while True:
        x=(rot((x+y+v[0]+f64(s,o+8))&M,37)*k1)&M
        y=(rot((y+v[1]+f64(s,o+48))&M,42)*k1)&M
        x^=w[1]; y=(y+v[0]+f64(s,o+40))&M
        z=(rot((z+w[0])&M,33)*k1)&M
        v=weaks(s,o,(v[1]*k1)&M,(x+w[0])&M)
        w=weaks(s,o+32,(z+w[1])&M,(y+f64(s,o+16))&M)
        z,x=x,z
        o+=64;n-=64
        if n==0: break
    return h16((h16(v[0],w[0])+sm(y)*k1+z)&M,(h16(v[1],w[1])+x)&M)
def pkgid(name): return cityhash64(name.lower().encode('utf-16le'))
