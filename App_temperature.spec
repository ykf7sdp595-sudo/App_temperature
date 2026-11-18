from pathlib import Path
from PyInstaller.utils.hooks import collect_all, copy_metadata

root = Path(SPECPATH)
datas, binaries, hiddenimports = collect_all('streamlit')
pdata, pbins, pimports = collect_all('plotly')
datas += pdata
binaries += pbins
hiddenimports += pimports
for package in ('streamlit', 'plotly', 'pandas', 'numpy', 'openpyxl', 'et_xmlfile'):
    datas += copy_metadata(package)
modules = ['data_io', 'chart_component']
datas += [(str(root / (name + '.py')), '.') for name in ['app'] + modules]
hiddenimports += modules + ['streamlit.web.bootstrap', 'openpyxl']
a = Analysis([str(root / 'launcher.py')], pathex=[str(root)], binaries=binaries,
             datas=datas, hiddenimports=hiddenimports, hookspath=[], hooksconfig={},
             runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='App_temperature',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=True)

