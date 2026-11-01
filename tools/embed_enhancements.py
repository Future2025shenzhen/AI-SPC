from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def embed(file,source,tag):
    p=ROOT/file
    text=p.read_text()
    start=f'<!-- {tag}:start -->'
    end=f'<!-- {tag}:end -->'
    if start in text:
        a=text.index(start);b=text.index(end,a)+len(end)
        text=text[:a]+text[b:]
    code=(ROOT/source).read_text()
    assert '</script' not in code.lower()
    pos=text.rfind('</body>')
    assert pos>=0
    text=text[:pos].rstrip()+'\n'+start+'\n<script>\n'+code+'\n</script>\n'+end+'\n'+text[pos:]
    p.write_text(text)
embed('DOE_Catapult_Competition.html','src/catapult-experience.js','catapult-experience')
embed('DOE_Catapult_Analysis.html','src/doe-workbench.js','doe-workbench')
(ROOT/'DOE_Catapult_Reference_Layout.html').write_bytes((ROOT/'DOE_Catapult_Competition.html').read_bytes())
(ROOT/'2K多响应变量DOE+投射器实验.html').write_bytes((ROOT/'DOE_Catapult_Analysis.html').read_bytes())
