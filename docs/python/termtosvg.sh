#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "${SCRIPT_DIR}" || exit 1

F=$1
TMPDIR=termtosvg.$$
OUTPUT=termtosvg.$$.ouput
rm -Rf "${TMPDIR}"
termtosvg --still-frames --screen-geometry 80x24 --template=solarized_light --command "python ${F}" "${TMPDIR}" >"${OUTPUT}" 2>&1
if test $? -ne 0; then
    echo "ERROR during termtosvg.sh $F, output:"
    cat "${OUTPUT}"
    exit 1
fi
NEWNAME="$(basename "${F}" .py).svg"
cp -f "${TMPDIR}/termtosvg_00000.svg" "${NEWNAME}"
rm -Rf "${TMPDIR}"
rm -Rf "${OUTPUT}"

echo "![rich output](docs/python/${NEWNAME})"
