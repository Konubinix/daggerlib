# [[file:../src/distroless.org::*Test script][Test script:1]]
source "./helpers.sh"

distroless_python3_code () {
      dagger call distroless-python-3-debian with-exec --args="python3","-c","import os; print(os.path.exists('/etc/localtime'))" stdout
}

distroless_python3_expected () {
      cat<<"EOEXPECTED"
True
EOEXPECTED
}

echo 'Run distroless_python3'

{ distroless_python3_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
distroless_python3_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying distroless_python3"
cat "${TMP}/stderr.txt" >&2
exit 1
}


distroless_static_export_code () {
      dagger call distroless-debian file --path="/etc/localtime" export --path="$TMP/out/localtime" > /dev/null
      test -s "$TMP/out/localtime" && echo "non-empty"
}

distroless_static_export_expected () {
      cat<<"EOEXPECTED"
non-empty
EOEXPECTED
}

echo 'Run distroless_static_export'

{ distroless_static_export_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
distroless_static_export_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying distroless_static_export"
cat "${TMP}/stderr.txt" >&2
exit 1
}
# Test script:1 ends here
