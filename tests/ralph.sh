# [[file:../src/ralph.org::*Test script][Test script:1]]
ROOT='/home/sam/prog/dagger'
source "./helpers.sh"

ralph_yml_valid_code () {
      dagger call debian --extra-packages="python3-yaml" with-file --path=/tmp/ralph.yml --source="${ROOT}/src/ralph.yml" with-exec --args="python3","-c","import yaml; d=yaml.safe_load(open('/tmp/ralph.yml')); print(d['event_loop']['starting_event']); print(len(d['hats']))" stdout
}

ralph_yml_valid_expected () {
      cat<<"EOEXPECTED"
work.start
2
EOEXPECTED
}

echo 'Run ralph_yml_valid'

{ ralph_yml_valid_code || true ; } > "${TMP}/code.txt" 2>/dev/null
ralph_yml_valid_expected > "${TMP}/expected.txt"
diff -uBw "${TMP}/code.txt" "${TMP}/expected.txt" || {
echo "Something went wrong when trying ralph_yml_valid"
exit 1
}
# Test script:1 ends here
