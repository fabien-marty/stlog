import argparse
import glob
import os
import sys
import random

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
parser = argparse.ArgumentParser(
    prog="termtosvg.py", description="wrapper to get some terminal screenshot"
)
parser.add_argument("filename")
parser.add_argument("--linting", action="store_true")
parser.add_argument("--pathprefix", type=str, default="")
parser.add_argument("--lines", type=int, default=10)
parser.add_argument("--columns", type=int, default=100)

args = parser.parse_args()

newname = os.path.basename(args.filename).replace(".py", ".svg")
path = os.path.join(SCRIPT_DIR, args.filename)
newpath = os.path.join(SCRIPT_DIR, newname)


def output_and_exit(pathprefix: str, newname: str):
    print(f"![rich output]({pathprefix}python/{newname})")
    sys.exit(0)


if args.linting:
    output_and_exit(args.pathprefix, newname)

rndint = random.randint(0, 1000000)
tmpdir = os.path.join(SCRIPT_DIR, f"termtosvg.{rndint}")
output = f"termtosvg.{rndint}.output"
os.system(f"rm -Rf {tmpdir} {output}")
cmd = f"termtosvg --still-frames --screen-geometry '{args.columns}x{args.lines}' --template=solarized_light --command 'python -u {path}' '{tmpdir}' >'{output}' 2>&1"
print(cmd)
rc = os.system(cmd)
os.system(f"cat {output}")
if rc != 0:
    print("ERROR during termtosvh, output:")
    os.system(f"cat {output}")
    sys.exit(1)

svg = sorted(glob.glob(os.path.join(tmpdir, "*.svg")))[-1]
os.system(f"cp -f {svg} {newpath}")
os.system(f"rm -Rf {tmpdir} {output}")
output_and_exit(args.pathprefix, newname)
