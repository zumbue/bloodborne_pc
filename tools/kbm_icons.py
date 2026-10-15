#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Builds builtin_mods/kbm_icons: the game's button prompts drawn as keyboard and mouse keys.

The pictures come from the "Customizable Keyboard and Mouse Icons for Bloodborne" mod (v1.5):
its Windows script (Bloodborne KBM Prompt Setup.bat) asks for a key per PS4 button, copies the
key's 32x32 DDS over the game's prompt texture (KG_R1.dds, ...), composes the stick and dialog
prompts with ImageMagick, converts them to BC7 with texconv and repacks menu/common.tpf.dcx with
WitchyBND. This script does the same steps on Linux: ImageMagick from the system, texconv and
WitchyBND (shipped by the mod) through Wine, in a throwaway prefix.

    python3 tools/kbm_icons.py "<mod folder or .zip>"

The keys are the defaults of runtime_pad.c (Dark Souls 3 layout); KEYS below names them with the
mod's file names. Rebuild after changing the default bindings.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / 'builtin_mods' / 'kbm_icons' / 'dvdroot_ps4' / 'menu' / 'common.tpf.dcx'

# PS4 prompt -> the mod's key picture (RESOURCES/PNG/*/<name>.png, RESOURCES/DDS/32x32/<name>.dds).
KEYS = {
    'menu_up': 'ARROW UP', 'menu_down': 'ARROW DOWN', 'menu_left': 'ARROW LEFT',
    'menu_right': 'ARROW RIGHT',
    'forward': 'W', 'backward': 'S', 'left': 'A', 'right': 'D',
    'r1': 'Left Click', 'r2': 'SHIFT LEFT CLICK', 'l1': 'SHIFT RIGHT CLICK', 'l2': 'Right Click',
    'triangle': 'F', 'circle': 'SPACE', 'square': 'R', 'cross': 'E',
    'r3': 'Middle Click', 'l3': 'X', 'touchpad_left': 'G', 'touchpad_right': 'TAB',
    'options': 'ESCAPE',
}
# Single prompts: the key's DDS replaces the texture as it is (the game calls Circle "OK").
SINGLE = {
    'KG_R1.dds': 'r1', 'KG_R2.dds': 'r2', 'KG_L1.dds': 'l1', 'KG_L2.dds': 'l2',
    'KG_R_U.dds': 'triangle', 'KG_OK.dds': 'circle', 'KG_R_L.dds': 'square',
    'KG_Cancel.dds': 'cross', 'KG_R3.dds': 'r3', 'KG_L3.dds': 'l3', 'KG_TP_L.dds': 'touchpad_left',
    'KG_TP_R.dds': 'touchpad_right', 'KG_Start.dds': 'options',
}
EMPTY = None
# Cross-shaped prompts (32x32): 10x10 keys at up, down, left, right.
CROSS_SLOTS = ((11, 5), (11, 15), (1, 15), (21, 15))
CROSS = {
    'KG_L_UDLR.dds': ('menu_up', 'menu_down', 'menu_left', 'menu_right'),
    'KG_L_UD.dds': ('menu_up', 'menu_down', EMPTY, EMPTY),
    'KG_L_U.dds': ('menu_up', EMPTY, EMPTY, EMPTY),
    'KG_L_D.dds': (EMPTY, 'menu_down', EMPTY, EMPTY),
    'KG_L_LR.dds': (EMPTY, EMPTY, 'menu_left', 'menu_right'),
    'KG_LS.dds': ('forward', 'backward', 'left', 'right'),
}
# The dialog footer (cancel, confirm, switch) drawn into MENU_Common_00091 at 26x26.
DIALOG = (('circle', 661, 123), ('cross', 694, 123), ('l3', 726, 123))


def run(*command, cwd=None, env=None):
    result = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, errors='replace')
    if result.returncode:
        sys.exit(f'{command[0]} failed ({result.returncode}):\n{result.stdout[-2000:]}')


def program_dir(source, work):
    """The mod's PROGRAM folder from its folder or its .zip."""
    source = Path(source)
    if source.is_file():
        with zipfile.ZipFile(source) as archive:
            archive.extractall(work / 'mod')
        source = work / 'mod'
    found = [p for p in source.rglob('PROGRAM') if (p / 'WITCHYBND' / 'WitchyBND.exe').is_file()]
    if not found:
        sys.exit(f'No PROGRAM/WITCHYBND/WitchyBND.exe in {source}: is it the KBM icons mod v1.5?')
    return found[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('mod', help='the mod folder or its .zip')
    parser.add_argument('--out', type=Path, default=OUT)
    args = parser.parse_args()
    for tool in ('magick', 'wine'):
        if not shutil.which(tool):
            sys.exit(f'{tool} is required (ImageMagick 7 and Wine)')
    with tempfile.TemporaryDirectory(prefix='kbm-icons-') as temp:
        work = Path(temp)
        program = program_dir(args.mod, work)
        res = program / 'RESOURCES'
        tpf = work / 'common-tpf-dcx'
        # Vanilla 1.09 textures, unpacked by the mod's author; the stick slot shows no mouse.
        shutil.copytree(res / 'TEMPLATES' / 'VANILLA FILES' / 'common-tpf-dcx', tpf)
        shutil.copy(res / 'DDS' / 'HARDCODED' / 'Empty Mouse.dds', tpf / 'KG_RS.dds')
        shutil.copy(res / 'TEMPLATES' / 'TRANSPARENT' / 'MENU_Common_00110.dds', tpf / 'MENU_Common_00110.dds')
        for texture, prompt in SINGLE.items():
            shutil.copy(res / 'DDS' / '32x32' / f'{KEYS[prompt]}.dds', tpf / texture)
        pngs = work / 'png'
        pngs.mkdir()
        empty = res / 'PNG' / '10x10' / '_EMPTY BOX.png'
        for texture, prompts in CROSS.items():
            command = ['magick', str(res / 'TEMPLATES' / '_EMPTY TEMPLATE.png')]
            for prompt, (x, y) in zip(prompts, CROSS_SLOTS):
                key = res / 'PNG' / '10x10' / f'{KEYS[prompt]}.png' if prompt else empty
                command += [str(key), '-geometry', f'+{x}+{y}', '-composite']
            run(*command, str(pngs / texture.replace('.dds', '.png')))
        command = ['magick', str(tpf / 'MENU_Common_00091.dds')]
        for prompt, x, y in DIALOG:
            command += ['(', str(res / 'PNG' / '32x32' / f'{KEYS[prompt]}.png'), '-filter', 'Lanczos',
                        '-define', 'filter:blur=0.9', '-resize', '26x26', ')',
                        '-geometry', f'+{x}+{y}', '-composite']
        run(*command, str(pngs / 'MENU_Common_00091.png'))
        env = dict(os.environ, WINEPREFIX=str(work / 'prefix'), WINEDEBUG='-all',
                   WINEDLLOVERRIDES='mscoree,mshtml=')
        texconv = next(p for p in (program / 'TEXCONV').iterdir() if p.name.casefold() == 'texconv.exe')
        run('wine', str(texconv), '-nologo', '-f', 'BC7_UNORM', '-y', '-o', 'Z:' + str(tpf),
            *('Z:' + str(p) for p in sorted(pngs.iterdir())), env=env)
        witchy = work / 'witchy'
        shutil.copytree(program / 'WITCHYBND', witchy, ignore=shutil.ignore_patterns('common*'))
        shutil.move(tpf, witchy / 'common-tpf-dcx')
        run('wine', 'WitchyBND.exe', '-r', '-s', 'common-tpf-dcx', 'common.tpf.dcx', cwd=witchy, env=env)
        built = witchy / 'common.tpf.dcx'
        if not built.is_file():
            sys.exit('WitchyBND wrote no common.tpf.dcx')
        args.out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(built, args.out)
    print(f'{args.out} ({args.out.stat().st_size} bytes)')


if __name__ == '__main__':
    main()
