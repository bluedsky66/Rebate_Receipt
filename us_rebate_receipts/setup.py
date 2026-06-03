from PyInstaller.__main__ import run

if __name__ == "__main__":
    run([
        'gui.py',
        '--name=US_Rebate_Receipt_Generator',
        '--onefile',
        '--windowed',
        '--add-data=config;config',
        '--add-data=output;output',
        '--add-data=jobs;jobs',
        '--clean',
        '--noconfirm'
    ])
