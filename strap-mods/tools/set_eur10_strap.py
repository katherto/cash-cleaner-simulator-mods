#!/usr/bin/env python3
"""Set the bill-strap (band) colour of the EUR 10 note in the NewBanknotes mod.

usage: set_eur10_strap.py <path to NewBanknotes_P.ucas> <path to NewBanknotes_P.utoc> <#RRGGBB>

The strap colour is the 'TapeColorB' vector parameter of MI_MoneyPack_EUR10.
Edit is in-place and size-preserving (12 bytes), so the .utoc is not modified.
The colour is given as sRGB hex (what you see in a colour picker) and stored as
linear float RGB, which is what Unreal materials use.
"""
import struct, sys, re
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import iostore

def srgb_to_linear(c):
    return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4

def main(ucas, utoc, hexcol):
    m = re.fullmatch(r'#?([0-9a-fA-F]{6})', hexcol)
    if not m: sys.exit('colour must look like #C8202B')
    v = m.group(1)
    rgb = [srgb_to_linear(int(v[i:i+2], 16)/255) for i in (0, 2, 4)]
    t = iostore.parse_toc(utoc)
    idx = [i for i, p in t['paths'].items() if p.endswith('Art/Money/MI_MoneyPack_EUR10.uasset')]
    assert len(idx) == 1, idx
    i = idx[0]
    chunk = iostore.read_chunk(t, ucas, i)
    # TapeColorB: the 4-float vector whose RGB is the old strap colour; locate by structure
    # (TapeColorA = cream 0.9219,0.8445,0.4993,1.0 sits 49 bytes before it)
    a = struct.pack('<4f', 0.921875, 0.8445, 0.4993, 1.0)
    pos_a = None
    for o in range(len(chunk)-16):
        f = struct.unpack_from('<4f', chunk, o)
        if abs(f[0]-0.9219) < 1e-3 and abs(f[1]-0.8445) < 1e-3 and abs(f[2]-0.4993) < 1e-3 and f[3] == 1.0:
            pos_a = o; break
    assert pos_a is not None, 'TapeColorA not found'
    pos_b = pos_a + 49
    old = struct.unpack_from('<4f', chunk, pos_b)
    assert old[3] == 1.0, old
    print('old TapeColorB (linear):', [round(x, 4) for x in old[:3]])
    new = chunk[:pos_b] + struct.pack('<3f', *rgb) + chunk[pos_b+12:]
    assert len(new) == len(chunk)
    # write back into the .ucas (uncompressed container: chunk bytes are contiguous)
    off, ln = t['offs'][i]
    bsz = t['bsz']
    first = off // bsz
    boff = t['blocks'][first][0]
    file_pos = boff + (off - first*bsz)
    # sanity: the chunk must be contiguous across the blocks it spans
    last = (off+ln-1)//bsz
    for b in range(first, last+1):
        assert t['blocks'][b][0] == boff + (b-first)*bsz, 'non-contiguous'
    with open(ucas, 'r+b') as f:
        f.seek(file_pos); assert f.read(ln) == chunk
        f.seek(file_pos + pos_b); f.write(struct.pack('<3f', *rgb))
    print('new TapeColorB (linear):', [round(x, 4) for x in rgb], '=', '#'+v.upper(), 'sRGB')

if __name__ == '__main__':
    if len(sys.argv) != 4: sys.exit(__doc__)
    main(*sys.argv[1:])
