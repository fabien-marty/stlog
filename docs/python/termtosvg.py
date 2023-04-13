import argparse
import re
import glob
import os
import sys
import random

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
parser = argparse.ArgumentParser(
    prog="termtosvg.py", description="wrapper to get some terminal screenshot"
)
parser.add_argument("filename")
parser.add_argument("--pathprefix", type=str, default="")
parser.add_argument("--lines", type=int, default=10)
parser.add_argument("--columns", type=int, default=100)
parser.add_argument("--interpreter", type=str, default="python")

args = parser.parse_args()

if "." not in args.filename:
    newname = args.filename.replace(" ", "") + ".svg"
else:
    newname = ".".join(os.path.basename(args.filename).split(".")[0:-1]) + ".svg"
if args.interpreter == "":
    path = args.filename
else:
    path = os.path.join(SCRIPT_DIR, args.filename)
newpath = os.path.join(SCRIPT_DIR, newname)


def output_and_exit(pathprefix: str, newname: str):
    print(f"![rich output]({pathprefix}python/{newname})")
    sys.exit(0)


if os.environ.get("CI", "false") == "true":
    output_and_exit(args.pathprefix, newname)

rndint = random.randint(0, 1000000)
tmpdir = os.path.join(SCRIPT_DIR, f"termtosvg.{rndint}")
output = f"termtosvg.{rndint}.output"
os.system(f"rm -Rf {tmpdir} {output}")
if args.interpreter:
    real_command=f"{args.interpreter} {path}"
else:
    real_command=path
cmd = f"termtosvg --still-frames --screen-geometry '{args.columns}x{args.lines}' --template=solarized_light --command '{real_command}' '{tmpdir}' >'{output}' 2>&1"
rc = os.system(cmd)
if rc != 0:
    print("ERROR during termtosvh, output:")
    os.system(f"cat {output}")
    sys.exit(1)

svg = sorted(glob.glob(os.path.join(tmpdir, "*.svg")))[-1]
with open(svg, "r") as f:
    svg_content = f.read()
    with open(svg + ".new", "w") as g:
        new_content = svg_content
        new_content = re.sub("0x[0-9a-z]*", "0x............", new_content)
        g.write(new_content)

os.system(f"diff {svg}.new {newpath} >/dev/null 2>&1 || cp -f {svg}.new {newpath}")
os.system(f"rm -Rf {tmpdir} {output}")
output_and_exit(args.pathprefix, newname)
