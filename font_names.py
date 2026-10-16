"""Print name-table IDs 1/2/4/6/16/17 and OS/2 weight for each TTF (no fontTools needed)."""
import struct, sys
from pathlib import Path


def tables(data):
    num = struct.unpack(">H", data[4:6])[0]
    out = {}
    for i in range(num):
        tag, _, off, length = struct.unpack(">4sIII", data[12 + 16 * i: 28 + 16 * i])
        out[tag.decode("latin-1")] = (off, length)
    return out


def names(data, off):
    _, count, str_off = struct.unpack(">HHH", data[off: off + 6])
    res = {}
    for i in range(count):
        pid, eid, lid, nid, ln, so = struct.unpack(">6H", data[off + 6 + 12 * i: off + 18 + 12 * i])
        raw = data[off + str_off + so: off + str_off + so + ln]
        if nid in (1, 2, 4, 6, 16, 17) and (pid, lid) in ((3, 0x409), (1, 0)):
            res.setdefault(nid, raw.decode("utf-16-be") if pid == 3 else raw.decode("mac_roman"))
    return res


def full_name(path):
    data = Path(path).read_bytes()
    return names(data, tables(data)["name"][0])[4]


if __name__ == "__main__":
    for f in sorted(Path(sys.argv[1]).rglob("*.ttf")):
        data = f.read_bytes()
        t = tables(data)
        weight = struct.unpack(">H", data[t["OS/2"][0] + 4: t["OS/2"][0] + 6])[0]
        n = names(data, t["name"][0])
        print(f"{f.stem:12} wght={weight}  " + "  ".join(f"{k}={v!r}" for k, v in sorted(n.items())))
