SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

export STLOG_ENV_JSON_CONTEXT='{"foo": "bar", "foo2": 123}'
python ${SCRIPT_DIR}/usage2.py