"""Create a deterministic, self-contained delivery bundle for the uploaded variant."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
names=['投射器实验_优化版.html','投射器实验_DOE分析_优化版.html','UPLOADED_CATAPULT_NOTES.md','start_uploaded_lab.py']
manifest={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}
out=ROOT/'downloads/catapult-upload-optimized.zip'
out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
    entries={name:(ROOT/name).read_bytes() for name in names}
    entries['SHA256.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode()
    for name,data in entries.items():
        info=zipfile.ZipInfo(name,date_time=(2026,11,1,0,0,0))
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=0o100644<<16
        archive.writestr(info,data,compresslevel=9)
with zipfile.ZipFile(out) as archive:
    assert archive.testzip() is None
    for name,digest in manifest.items():
        assert hashlib.sha256(archive.read(name)).hexdigest()==digest
print(f'Packaged {out.name}: {out.stat().st_size:,} bytes; all SHA-256 checks passed')
