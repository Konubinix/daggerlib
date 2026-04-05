# [[file:../doc/docker_in_docker.org::*Test script][Test script:1]]
source "./helpers.sh"

dind_docker_version_code () {
      dagger call dind-container with-exec --args="docker","--version" stdout
}

dind_docker_version_expected () {
      cat<<"EOEXPECTED"
Docker version 29.3.1, build c2be9cc
EOEXPECTED
}

echo 'Run dind_docker_version'

{ dind_docker_version_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
dind_docker_version_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying dind_docker_version"
cat "${TMP}/stderr.txt" >&2
exit 1
}


dind_docker_info_code () {
      dagger call dind-with-docker --cmd="docker info --format '{{.OSType}}'" stdout
}

dind_docker_info_expected () {
      cat<<"EOEXPECTED"
linux
EOEXPECTED
}

echo 'Run dind_docker_info'

{ dind_docker_info_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
dind_docker_info_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying dind_docker_info"
cat "${TMP}/stderr.txt" >&2
exit 1
}
# Test script:1 ends here
