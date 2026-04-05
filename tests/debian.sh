# [[file:../src/debian.org::*Test script][Test script:1]]
source "./helpers.sh"

debian_timezone_code () {
      dagger call debian with-exec --args="sh","-c","readlink -f /etc/localtime" stdout
}

debian_timezone_expected () {
      cat<<"EOEXPECTED"
/usr/share/zoneinfo/Europe/Paris
EOEXPECTED
}

echo 'Run debian_timezone'

{ debian_timezone_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
debian_timezone_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying debian_timezone"
cat "${TMP}/stderr.txt" >&2
exit 1
}


debian_no_recommends_code () {
      dagger call debian with-exec --args="cat","/etc/apt/apt.conf.d/01norecommend" stdout
}

debian_no_recommends_expected () {
      cat<<"EOEXPECTED"
APT::Install-Recommends "0";
APT::Install-Suggests "0";
EOEXPECTED
}

echo 'Run debian_no_recommends'

{ debian_no_recommends_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
debian_no_recommends_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying debian_no_recommends"
cat "${TMP}/stderr.txt" >&2
exit 1
}


debian_extra_packages_code () {
      dagger call debian --extra-packages=curl with-exec --args="which","curl" stdout
}

debian_extra_packages_expected () {
      cat<<"EOEXPECTED"
/usr/bin/curl
EOEXPECTED
}

echo 'Run debian_extra_packages'

{ debian_extra_packages_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
debian_extra_packages_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying debian_extra_packages"
cat "${TMP}/stderr.txt" >&2
exit 1
}


debian_user_check_code () {
      dagger call debian-user with-exec --args="id","sam" stdout
}

debian_user_check_expected () {
      cat<<"EOEXPECTED"
uid=1000(sam) gid=1000(sam) groups=1000(sam),100(users)
EOEXPECTED
}

echo 'Run debian_user_check'

{ debian_user_check_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
debian_user_check_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying debian_user_check"
cat "${TMP}/stderr.txt" >&2
exit 1
}


debian_python_user_venv_check_code () {
      dagger call debian-python-user-venv with-exec --args="sh","-c","test -d /app/venv && /app/venv/bin/python --version" stdout
}

debian_python_user_venv_check_expected () {
      cat<<"EOEXPECTED"
Python 3.13.5
EOEXPECTED
}

echo 'Run debian_python_user_venv_check'

{ debian_python_user_venv_check_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
debian_python_user_venv_check_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying debian_python_user_venv_check"
cat "${TMP}/stderr.txt" >&2
exit 1
}


debian_europe_paris_export_code () {
      dagger call debian-europe-paris export --path="$TMP/out/localtime" > /dev/null
      test -s "$TMP/out/localtime" && echo "non-empty"
}

debian_europe_paris_export_expected () {
      cat<<"EOEXPECTED"
non-empty
EOEXPECTED
}

echo 'Run debian_europe_paris_export'

{ debian_europe_paris_export_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
debian_europe_paris_export_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying debian_europe_paris_export"
cat "${TMP}/stderr.txt" >&2
exit 1
}
# Test script:1 ends here
