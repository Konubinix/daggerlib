# [[file:../src/flask_venv.org::*Test script][Test script:1]]
source "./helpers.sh"

flask_venv_export_code () {
      dagger call flask-venv export --path="$TMP/out" > /dev/null
      test -f "$TMP/out/bin/flask" && echo "bin/flask exists"
}

flask_venv_export_expected () {
      cat<<"EOEXPECTED"
bin/flask exists
EOEXPECTED
}

echo 'Run flask_venv_export'

{ flask_venv_export_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
flask_venv_export_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying flask_venv_export"
cat "${TMP}/stderr.txt" >&2
exit 1
}
# Test script:1 ends here
