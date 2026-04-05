# [[file:../src/pip_tools.org::*Test script][Test script:1]]
source "./helpers.sh"

pip_tools_available_code () {
      dagger call pip-tools with-exec --args="which","pip-compile" stdout
}

pip_tools_available_expected () {
      cat<<"EOEXPECTED"
/home/sam/.local/bin/pip-compile
EOEXPECTED
}

echo 'Run pip_tools_available'

{ pip_tools_available_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
pip_tools_available_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying pip_tools_available"
cat "${TMP}/stderr.txt" >&2
exit 1
}
# Test script:1 ends here
