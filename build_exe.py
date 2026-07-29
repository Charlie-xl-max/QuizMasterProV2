# -*- coding: utf-8 -*-
"""
QuizMasterPro V2 - PyInstaller 打包脚本
Copyright (c) 2026 QuizMasterPro V2 Contributors
Licensed under the MIT License (see LICENSE file for details)

Pack into single .exe, no Python environment needed
"""
import os
import sys
import shutil
import subprocess

# Force UTF-8 on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def clean():
    for d in ['build', 'dist']:
        p = os.path.join(BASE_DIR, d)
        if os.path.exists(p):
            shutil.rmtree(p)
            print(f"  Cleaned: {d}")
    for f in os.listdir(BASE_DIR):
        if f.endswith('.spec'):
            os.remove(os.path.join(BASE_DIR, f))


def build():
    print("=" * 60)
    print("  QuizMasterPro V2 - Build EXE")
    print("=" * 60)

    clean()

    print("\n[1/2] Building with PyInstaller...")

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--clean',
        '--onefile',
        '--console',
        '--name', 'QuizMasterProV2',

        '--hidden-import', 'uvicorn.logging',
        '--hidden-import', 'uvicorn.loops',
        '--hidden-import', 'uvicorn.loops.auto',
        '--hidden-import', 'uvicorn.protocols',
        '--hidden-import', 'uvicorn.protocols.http',
        '--hidden-import', 'uvicorn.protocols.http.auto',
        '--hidden-import', 'uvicorn.protocols.websockets',
        '--hidden-import', 'uvicorn.protocols.websockets.auto',
        '--hidden-import', 'uvicorn.lifespan',
        '--hidden-import', 'uvicorn.lifespan.on',

        '--hidden-import', 'fastapi',
        '--hidden-import', 'pydantic',
        '--hidden-import', 'pydantic.deprecated',
        '--hidden-import', 'pydantic.deprecated.class_validators',
        '--hidden-import', 'pydantic.deprecated.decorator',

        '--hidden-import', 'sqlalchemy',
        '--hidden-import', 'sqlalchemy.dialects.sqlite',

        '--hidden-import', 'docx',
        '--hidden-import', 'pdfplumber',
        '--hidden-import', 'pdfplumber.pdf',
        '--hidden-import', 'PyPDF2',
        '--hidden-import', 'PIL',

        '--add-data', f'index.html{os.pathsep}.',
        '--add-data', f'question_parser.py{os.pathsep}.',
        '--add-data', f'questions.js{os.pathsep}.',

        'main.py',
    ]

    result = subprocess.run(cmd, cwd=BASE_DIR)

    print("\n[2/2] Result:")
    if result.returncode == 0:
        exe_path = os.path.join(BASE_DIR, 'dist', 'QuizMasterProV2.exe')
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print("=" * 60)
        print(f"  SUCCESS!")
        print(f"  File: {exe_path}")
        print(f"  Size: {size_mb:.1f} MB")
        print("=" * 60)
        print("\n  How to use:")
        print("  1. Double-click QuizMasterProV2.exe")
        print("  2. Browser opens automatically")
        print("  3. Upload your question bank files (.docx/.pdf/.zip)")
        print("  4. Start practicing!")
        print("  5. All data saved in data/ folder next to the EXE")
    else:
        print("=" * 60)
        print(f"  FAILED! Error code: {result.returncode}")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    build()
