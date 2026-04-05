# [[file:../doc/production_images.org::*Test script][Test script:1]]
source "./helpers.sh"

tz_artifacts_code () {
      dagger call alpine-tz export --path="$TMP/out" > /dev/null
      ls "$TMP/out" | sort
}

tz_artifacts_expected () {
      cat<<"EOEXPECTED"
localtime
timezone
EOEXPECTED
}

echo 'Run tz_artifacts'

{ tz_artifacts_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
tz_artifacts_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying tz_artifacts"
cat "${TMP}/stderr.txt" >&2
exit 1
}


distroless_python_code () {
      dagger call distroless-python-3-debian with-exec --args="python3","-c","import os; print(os.path.exists('/etc/localtime'))" stdout
}

distroless_python_expected () {
      cat<<"EOEXPECTED"
True
EOEXPECTED
}

echo 'Run distroless_python'

{ distroless_python_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
distroless_python_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying distroless_python"
cat "${TMP}/stderr.txt" >&2
exit 1
}


distroless_static_code () {
      dagger call distroless-debian file --path="/etc/localtime" export --path="$TMP/out2/localtime" > /dev/null
      test -s "$TMP/out2/localtime" && echo "non-empty"
}

distroless_static_expected () {
      cat<<"EOEXPECTED"
non-empty
EOEXPECTED
}

echo 'Run distroless_static'

{ distroless_static_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
distroless_static_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying distroless_static"
cat "${TMP}/stderr.txt" >&2
exit 1
}
# Test script:1 ends here
