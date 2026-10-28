import sys, json, concurrent.futures as cf
sys.path.insert(0, __file__.rsplit('/',1)[0]); import commons as C
fs=[l.strip().removeprefix('File:') for l in sys.stdin if l.strip().startswith('File:') or (l.strip() and not l.startswith('SUBS'))]
fs=[f for f in fs if not f.lower().endswith(('.ogg','.svg','.pdf','.webm','.ogv','.tif','.djvu','.wav','.mp3'))]
with cf.ThreadPoolExecutor(3) as ex:
    for i in ex.map(C.info, fs):
        ok = 'FREE' if C.free(i) else 'no  '
        print(f"{ok} {i['w']}x{i['h']} | {i['file'][:95]} | {','.join(i['lic'])[:40]} | {i['date'][:30]} | {i['desc'][:150]}")
