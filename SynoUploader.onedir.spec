# -*- mode: python -*-

block_cipher = None


a = Analysis(['SynoUploader.py'],
             pathex=['Z:\\code\\SynoUploader'],
             binaries=[],
             datas=[('icons','icons'),('setting.cfg','')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='SynoUploader',
          debug=False,
          strip=False,
          upx=True,
          console=True , icon='icons\\SynoUploader.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='SynoUploader')
