from pathlib import Path
import nbformat
ROOT=Path(__file__).resolve().parents[1]

def test_all_notebooks_parse():
    notebooks=list(ROOT.rglob('*.ipynb'))
    assert len(notebooks)>=55
    for p in notebooks:
        nbformat.validate(nbformat.read(p,as_version=4))

def test_six_domains_per_chapter():
    for ch in (ROOT/'notebooks').iterdir():
        if ch.is_dir():
            assert len(list(ch.glob('*.ipynb')))==6

def test_no_embedded_obvious_api_key():
    for p in ROOT.rglob('*.ipynb'):
        s=p.read_text(encoding='utf-8')
        assert 'YOUR_REAL_PRIVATE_API_KEY' not in s
