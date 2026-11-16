"""pack059_import.py <previous 059 import zip> <OROR jar> <CHANGES md> <out.zip> [label]: the next 059 import zip from the
last one the user has (059e onwards): OROR's jar and the 059 notes replaced, the first-read note's latest lines added,
the manifest's version moved on; every other entry copied as it was, byte for byte.

OROR's jar is written with its small entries (under 64 KB since 059g: the many JSON models, lang files, classes) stored rather
than deflated, so that the import zip's own deflate takes them together: the same entries, checked by CRC, and the
import zip about half a megabyte smaller (it must stay under 30,000,000 bytes).

(059f) kept in the repository: the 059e builder lived outside it and was lost with a container.

(059h) The pictures (PNG) in OROR's jar are packed tighter, pixel for pixel the same (their image data deflated again at
zlib's best, text and time chunks dropped; checked: header, palette, transparency and scanlines unchanged): 059h's
import zip was 65,738 bytes over the limit, and this takes some 200 KB off."""
import io, json, os, struct, sys, zipfile, zlib

src, jar, notes, out = sys.argv[1:5]
label = sys.argv[5] if len(sys.argv) > 5 else '059g'
JAR_NAME = 'overrides/mods/oror_supreme_bosses-0.17.39-059-preview.jar'
NOTES_NAME = 'overrides/CHANGES_0.17.39-059_JA.md'
FIRST = 'README_FIRST_059_JA.txt'
FIRST_ADD = {
    '059f': ('・059f：ORORの神格・王国兵もガード・パリイします（構え・払い・防御の動き、火花と金属音のエフェクト）。\n'
             '・059f：「王都の羅針盤」：世界に初めて入ったときに1つもらえます（コンパス・金3・エメラルドでも作れます）。\n'
             '  針は王都（村人王の宮殿）を指し、右クリックで距離と方角が出ます。\n'
             '・059f：砲台の前の胸壁・壁を広く取り払い、門の塔にふさがれていた城壁の砲郭8基は城壁の上へ上げました。\n'
             '  畑の中に立っていた対空砲6基は、足元を石の台にして畑をなくしました。\n'
             '・059f：王都の中では火事が広がらず、敵モブがブロックを壊せません。崩壊王の「消去」で宮殿に穴が残る不具合を直し、\n'
             '  エラーを出したブロック（機械など）でサーバーが止まらないようにしました。\n'),
    '059g': ('・059g：ORORの人型30人の頭（顔と髪）を作り直しました。目は白目と瞳の2色、口・鼻なし、頬に淡いピンク、\n'
             '  前髪は目の上まで、頬にかかる横髪。体・服・武器の形は前のままです。\n'
             '・059g：デミウルゴス・テイア・クールマ・淵煌・バハムートを、デザイン画に合わせて作り直しました。\n'
             '・059g：王都の畑の上に立っていた塔・建物・台のある区画は畑をやめ、門のそばで壁や柵を向いていた砲10基の向きを直しました\n'
             '  （今の世界には `/oror citadel update on` で反映、更新表57版）。\n'),
    '059h': ('・059h：戦うモブ（敵・村人・王国兵・神々）が、当たる寸前に攻撃や矢をさっとよけます（後ろからは不可）。\n'
             '  強くレベルの高い、経験を積んだモブほどうまく、スタミナも多く、同じモブでも個体ごとに違います。\n'
             '  スタミナは回避・防御・攻撃で減り、切れると息切れして回避も防御もできません（頭の上に細いゲージ）。\n'
             '・059h：神々の体力は10万、攻撃力は10〜50倍。村人王は体力1万、王国の位の人は5〜10倍です。\n'
             '・059h：王国の兵が据え置きの砲台（TOWを含む5種）に乗って撃ち、A-10が飛んで攻撃し、滑走路に降ります。\n'
             '  村人は村と村、王国をまたいで行き来・取引し、銃や戦車を作り、機械の燃料を村の石炭・木炭で補います。\n'),
}


PNG_SIG = b'\x89PNG\r\n\x1a\n'
PNG_DROP = (b'tEXt', b'zTXt', b'iTXt', b'tIME')   # text and time only: every chunk that bears on the picture is kept


def png_chunks(d):
    pos, out = 8, []
    while pos + 8 <= len(d):
        ln = struct.unpack('>I', d[pos:pos + 4])[0]
        out.append((d[pos + 4:pos + 8], d[pos + 8:pos + 8 + ln]))
        pos += 12 + ln
    return out


def png_image(d):
    """What a PNG shows: its header, palette and transparency, and its filtered scanlines (the IDAT stream unpacked)."""
    ch = png_chunks(d)
    keep = tuple((t, b) for t, b in ch if t in (b'IHDR', b'PLTE', b'tRNS'))
    return keep, zlib.decompress(b''.join(b for t, b in ch if t == b'IDAT'))


def png_smaller(d):
    """(059h) The same picture in fewer bytes: its image data deflated again at the best of zlib's settings, its text and
    time chunks dropped; the scanlines, filters, palette and every other chunk kept as they were. None if not smaller."""
    if d[:8] != PNG_SIG:
        return None
    try:
        ch = png_chunks(d)
        raw = zlib.decompress(b''.join(b for t, b in ch if t == b'IDAT'))
    except Exception:
        return None
    best = None
    for level, mem, strat in ((9, 8, zlib.Z_DEFAULT_STRATEGY), (9, 9, zlib.Z_DEFAULT_STRATEGY), (9, 9, zlib.Z_FILTERED)):
        c = zlib.compressobj(level, zlib.DEFLATED, 15, mem, strat)
        z = c.compress(raw) + c.flush()
        if best is None or len(z) < len(best):
            best = z
    out = [PNG_SIG]
    idat_done = False
    for t, b in ch:
        if t in PNG_DROP:
            continue
        if t == b'IDAT':
            if idat_done:
                continue
            idat_done = True
            b = best
        out.append(struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b) & 0xffffffff))
    new = b''.join(out)
    return new if len(new) < len(d) else None


def repack(data):
    zin = zipfile.ZipFile(io.BytesIO(data))
    buf = io.BytesIO()
    shrunk = 0
    with zipfile.ZipFile(buf, 'w') as z:
        for i in zin.infolist():
            d = zin.read(i.filename)
            if i.filename.endswith('.png'):
                # (059h) the import zip was 65,738 bytes over 30,000,000: the pictures packed tighter, pixel for pixel the same
                smaller = png_smaller(d)
                if smaller is not None:
                    shrunk += len(d) - len(smaller)
                    d = smaller
            ni = zipfile.ZipInfo(i.filename, date_time=i.date_time)
            ni.external_attr = i.external_attr
            # (059g) entries under 64 KB stored for the import zip's own deflate, the rest deflated at level 9
            if len(d) < 65536:
                ni.compress_type = zipfile.ZIP_STORED
                z.writestr(ni, d)
            else:
                ni.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(ni, d, compresslevel=9)
    # the same entries, byte for byte; (059h) the pictures the same pixel for pixel (header, palette, transparency, scanlines)
    zr = zipfile.ZipFile(io.BytesIO(buf.getvalue()))
    assert zin.namelist() == zr.namelist(), 'repacked jar lists other entries'
    for i in zin.infolist():
        before, after = zin.read(i.filename), zr.read(i.filename)
        if before == after:
            continue
        assert i.filename.endswith('.png') and png_image(before) == png_image(after), 'repacked jar differs: ' + i.filename
    print(json.dumps({'pngBytesSaved': shrunk}))
    return buf.getvalue()


def main():
    zin = zipfile.ZipFile(src)
    names = zin.namelist()
    assert JAR_NAME in names and NOTES_NAME in names, 'not a 059 import zip'
    jar_bytes = repack(open(jar, 'rb').read())
    notes_bytes = open(notes, 'rb').read()
    if os.path.exists(out):
        os.remove(out)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for i in zin.infolist():
            n = i.filename
            data = zin.read(n)
            if n == JAR_NAME:
                data = jar_bytes
            elif n == NOTES_NAME:
                data = notes_bytes
            elif n == FIRST:
                text = data.decode('utf-8')
                for key in [k for k in ('059f', '059g', '059h') if k <= label]:
                    add = FIRST_ADD[key]
                    if add.splitlines()[0] not in text:
                        mark = '・058：'
                        text = text.replace(mark, add + mark, 1) if mark in text else text + add
                data = text.encode('utf-8')
            elif n == 'manifest.json':
                m = json.loads(data)
                m['version'] = '0.17.39-' + label + '-preview'
                data = json.dumps(m, ensure_ascii=False, indent=2).encode('utf-8')
            z.writestr(i, data)
    size = os.path.getsize(out)
    print(json.dumps({'out': out, 'bytes': size, 'under30MB': size < 30_000_000, 'entries': len(names)}))


if __name__ == '__main__':
    main()
