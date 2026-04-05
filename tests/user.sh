# [[file:../src/user.org::*Test script][Test script:1]]
source "./helpers.sh"

use_user_whoami_code () {
      dagger call alpine-user with-exec --args="whoami" stdout
}

use_user_whoami_expected () {
      cat<<"EOEXPECTED"
sam
EOEXPECTED
}

echo 'Run use_user_whoami'

{ use_user_whoami_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
use_user_whoami_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying use_user_whoami"
cat "${TMP}/stderr.txt" >&2
exit 1
}


use_user_workdir_code () {
      dagger call alpine-user with-exec --args="pwd" stdout
}

use_user_workdir_expected () {
      cat<<"EOEXPECTED"
/home/sam
EOEXPECTED
}

echo 'Run use_user_workdir'

{ use_user_workdir_code || true ; } > "${TMP}/code.txt" 2>"${TMP}/stderr.txt"
use_user_workdir_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying use_user_workdir"
cat "${TMP}/stderr.txt" >&2
exit 1
}
# Test script:1 ends here
