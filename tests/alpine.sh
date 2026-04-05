# [[file:../src/alpine.org::*Test script][Test script:1]]
source "./helpers.sh"

alpine_timezone_code () {
      dagger call alpine with-exec --args="cat","/etc/timezone" stdout
}

alpine_timezone_expected () {
      cat<<"EOEXPECTED"
Europe/Paris
EOEXPECTED
}

echo 'Run alpine_timezone'

{ alpine_timezone_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
alpine_timezone_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying alpine_timezone"
cat "${TMP}/stderr.txt" >&2
exit 1
}


alpine_extra_packages_code () {
      dagger call alpine --extra-packages=curl with-exec --args="which","curl" stdout
}

alpine_extra_packages_expected () {
      cat<<"EOEXPECTED"
/usr/bin/curl
EOEXPECTED
}

echo 'Run alpine_extra_packages'

{ alpine_extra_packages_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
alpine_extra_packages_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying alpine_extra_packages"
cat "${TMP}/stderr.txt" >&2
exit 1
}


alpine_user_check_code () {
      dagger call alpine-user with-exec --args="id","sam" stdout
}

alpine_user_check_expected () {
      cat<<"EOEXPECTED"
uid=1000(sam) gid=1000(sam) groups=1000(sam),1000(sam)
EOEXPECTED
}

echo 'Run alpine_user_check'

{ alpine_user_check_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
alpine_user_check_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying alpine_user_check"
cat "${TMP}/stderr.txt" >&2
exit 1
}


alpine_tz_export_code () {
      dagger call alpine-tz export --path="$TMP/out" > /dev/null
      ls "$TMP/out" | sort
}

alpine_tz_export_expected () {
      cat<<"EOEXPECTED"
localtime
timezone
EOEXPECTED
}

echo 'Run alpine_tz_export'

{ alpine_tz_export_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
alpine_tz_export_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying alpine_tz_export"
cat "${TMP}/stderr.txt" >&2
exit 1
}


alpine_python_check_code () {
      dagger call alpine-python with-exec --args="python3","--version" stdout
}

alpine_python_check_expected () {
      cat<<"EOEXPECTED"
Python 3.12.12
EOEXPECTED
}

echo 'Run alpine_python_check'

{ alpine_python_check_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
alpine_python_check_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying alpine_python_check"
cat "${TMP}/stderr.txt" >&2
exit 1
}


alpine_python_user_venv_check_code () {
      dagger call alpine-python-user-venv with-exec --args="sh","-c","test -d /app/venv && /app/venv/bin/python --version" stdout
}

alpine_python_user_venv_check_expected () {
      cat<<"EOEXPECTED"
Python 3.12.12
EOEXPECTED
}

echo 'Run alpine_python_user_venv_check'

{ alpine_python_user_venv_check_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
alpine_python_user_venv_check_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying alpine_python_user_venv_check"
cat "${TMP}/stderr.txt" >&2
exit 1
}
# Test script:1 ends here
