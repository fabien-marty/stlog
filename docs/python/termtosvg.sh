#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "${SCRIPT_DIR}" || exit 1

F=$1
PATHPREFIX=${2:-}
LINES=${3:-10}


TMPDIR=termtosvg.$$
OUTPUT=termtosvg.$$.ouput
rm -Rf "${TMPDIR}"
termtosvg --still-frames --screen-geometry "100x${LINES}" --template=solarized_light --command "python -u ${F}" "${TMPDIR}" >"${OUTPUT}" 2>&1
if test $? -ne 0; then
    echo "ERROR during termtosvg.sh $F, output:"
    cat "${OUTPUT}"
    exit 1
fi
NEWNAME=$(basename "${F}" .py).svg
OLDNAME=$(ls ${TMPDIR}/*.svg |tail -1)
cp -f "${OLDNAME}" "${NEWNAME}"
rm -Rf "${TMPDIR}"
rm -Rf "${OUTPUT}"

echo "![rich output](${PATHPREFIX}python/${NEWNAME})"
