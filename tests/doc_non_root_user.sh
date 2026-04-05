# [[file:../doc/non_root_user.org::*Test script][Test script:1]]
source "./helpers.sh"

alpine_user_whoami_code () {
      dagger call alpine-user with-exec --args="whoami" stdout
}

alpine_user_whoami_expected () {
      cat<<"EOEXPECTED"
sam
EOEXPECTED
}

echo 'Run alpine_user_whoami'

{ alpine_user_whoami_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
alpine_user_whoami_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying alpine_user_whoami"
cat "${TMP}/stderr.txt" >&2
exit 1
}


alpine_user_home_code () {
      dagger call alpine-user with-exec --args="pwd" stdout
}

alpine_user_home_expected () {
      cat<<"EOEXPECTED"
/home/sam
EOEXPECTED
}

echo 'Run alpine_user_home'

{ alpine_user_home_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
alpine_user_home_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying alpine_user_home"
cat "${TMP}/stderr.txt" >&2
exit 1
}


alpine_user_id_code () {
      dagger call alpine-user with-exec --args="id","sam" stdout
}

alpine_user_id_expected () {
      cat<<"EOEXPECTED"
uid=1000(sam) gid=1000(sam) groups=1000(sam),1000(sam)
EOEXPECTED
}

echo 'Run alpine_user_id'

{ alpine_user_id_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
alpine_user_id_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying alpine_user_id"
cat "${TMP}/stderr.txt" >&2
exit 1
}


debian_user_id_code () {
      dagger call debian-user with-exec --args="id","sam" stdout
}

debian_user_id_expected () {
      cat<<"EOEXPECTED"
uid=1000(sam) gid=1000(sam) groups=1000(sam),100(users)
EOEXPECTED
}

echo 'Run debian_user_id'

{ debian_user_id_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
debian_user_id_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying debian_user_id"
cat "${TMP}/stderr.txt" >&2
exit 1
}
# Test script:1 ends here
