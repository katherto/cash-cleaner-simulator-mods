import sys,struct,os,zipfile,shutil; sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
import iostore, merge as M, iobuild2 as B2, cityhash as C, make_gbp as G
S='/tmp/claude-0/-home-claude/d45f1c92-efff-57ad-9047-c8850f26cabc/scratchpad/'
P=S+'addon12/CashCleanerSimulator/Content/Paks/~mods/NewBanknotes_AddonStrapFix_P'
CHAIN=['CashCleanerSimulator','Content','Art','Money']
def load():
    t=iostore.parse_toc(P+'.utoc'); n=len(t['ids']); hdr=M.parse_header(iostore.read_chunk(t,P+'.ucas',n-1))
    names=['MI_MoneyPack_EUR05','MI_MoneyPack_EUR10','MI_MoneyPack_EUR100']
    return {nm:(hdr[3][k],iostore.read_chunk(t,P+'.ucas',k),hdr[4][k]) for k,nm in enumerate(names)}
def orig5(pid):
    OR=S+'mod_orig/CashCleanerSimulator/Content/Paks/~mods/NewBanknotes_P'
    to=iostore.parse_toc(OR+'.utoc')
    for i,c in enumerate(to['ids']):
        c=bytes(c)
        if struct.unpack('<Q',c[:8])[0]==pid and 1 in (c[10],c[11]): return iostore.read_chunk(to,OR+'.ucas',i)
def build(names_data, order_sorted=True):
    items=[(nm+'.uasset',pid,d,imps) for nm,(pid,d,imps) in names_data]
    if order_sorted: items.sort(key=lambda x:x[1])
    utoc,ucas=B2.build_container('NewBanknotes_AddonStrapFix_P',CHAIN,items)
    offs={}
    for k,it in enumerate(items):
        blk=int.from_bytes(utoc[144+12*len(items)+12+0:0],'little') if False else None
    return items,utoc,ucas
