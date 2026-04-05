# [[file:../doc/python_environment.org::*Test script][Test script:1]]
source "./helpers.sh"

python_version_code () {
      dagger call alpine-python with-exec --args="python3","-c","import sys; v=sys.version_info; print('3.10+' if v.major*100+v.minor >= 310 else 'too old')" stdout
}

python_version_expected () {
      cat<<"EOEXPECTED"
3.10+
EOEXPECTED
}

echo 'Run python_version'

{ python_version_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
python_version_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying python_version"
cat "${TMP}/stderr.txt" >&2
exit 1
}


alpine_venv_code () {
      dagger call alpine-python-user-venv with-exec --args="/app/venv/bin/python","-c","import sys; v=sys.version_info; print('3.10+' if v.major*100+v.minor >= 310 else 'too old')" stdout
}

alpine_venv_expected () {
      cat<<"EOEXPECTED"
3.10+
EOEXPECTED
}

echo 'Run alpine_venv'

{ alpine_venv_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
alpine_venv_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying alpine_venv"
cat "${TMP}/stderr.txt" >&2
exit 1
}


venv_with_packages_code () {
      dagger call alpine-python-user-venv --packages=requests with-exec --args="python3","-c","import requests; print(requests.__name__)" stdout
}

venv_with_packages_expected () {
      cat<<"EOEXPECTED"
requests
EOEXPECTED
}

echo 'Run venv_with_packages'

{ venv_with_packages_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
venv_with_packages_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying venv_with_packages"
cat "${TMP}/stderr.txt" >&2
exit 1
}


debian_venv_code () {
      dagger call debian-python-user-venv with-exec --args="/app/venv/bin/python","-c","import sys; v=sys.version_info; print('3.10+' if v.major*100+v.minor >= 310 else 'too old')" stdout
}

debian_venv_expected () {
      cat<<"EOEXPECTED"
3.10+
EOEXPECTED
}

echo 'Run debian_venv'

{ debian_venv_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
debian_venv_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying debian_venv"
cat "${TMP}/stderr.txt" >&2
exit 1
}


pip_tools_code () {
      dagger call pip-tools with-exec --args="which","pip-compile" stdout
}

pip_tools_expected () {
      cat<<"EOEXPECTED"
/home/sam/.local/bin/pip-compile
EOEXPECTED
}

echo 'Run pip_tools'

{ pip_tools_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
pip_tools_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying pip_tools"
cat "${TMP}/stderr.txt" >&2
exit 1
}
# Test script:1 ends here
