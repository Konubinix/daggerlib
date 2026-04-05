# [[file:../doc/base_containers.org::*Test script][Test script:1]]
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


distroless_static_tz_code () {
      dagger call distroless-debian file --path="/etc/localtime" export --path="$TMP/out/localtime" > /dev/null
      test -s "$TMP/out/localtime" && echo "non-empty"
}

distroless_static_tz_expected () {
      cat<<"EOEXPECTED"
non-empty
EOEXPECTED
}

echo 'Run distroless_static_tz'

{ distroless_static_tz_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
distroless_static_tz_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying distroless_static_tz"
cat "${TMP}/stderr.txt" >&2
exit 1
}
# Test script:1 ends here
