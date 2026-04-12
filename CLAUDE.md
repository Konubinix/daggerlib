Use those scripts only:
- ./bootstrap.sh
- ./init-examples.sh (runs init-examples-host.sh in a dagger container)
- ./init-examples-host.sh (host emacs, called by init-examples.sh)
- ./tangle.sh (runs tangle-host.sh in a dagger container)
- ./tangle-host.sh (host emacs, called by tangle.sh)
- ./run.sh (runs run-host.sh in a dagger container)
- ./run-host.sh (host emacs, called by run.sh)
- ./test.sh
- ./test-dind.sh

After editing org files, always run the full pipeline:
1. ./tangle.sh
2. ./run.sh (in doubt, always run — it's fast if not needed)
3. ./tangle.sh (again — run.sh may create directories that tangle needs)
4. ./test.sh

If ./tangle.sh fails because the module can't load (e.g. syntax error
in tangled Python after editing org), use ./tangle-host.sh to tangle
locally and break the chicken-and-egg cycle. Then resume with ./tangle.sh.

When creating a new example, add ./init-examples.sh before step 1
to bootstrap the dagger project (runs :init yes blocks).

Use ./init-examples.sh --from-scratch only when refactoring the init
blocks themselves — it wipes all generated files and re-runs init from
zero. Never use it just because content changed.

If the tooling does not work. Focus on fixing it. The tooling must be helpful
and help me when something goes wrong. If the tooling does not help, improve the
tooling, don't workaround.

Don't piss code. Always plan.

If you think something goes wrong, search for answers in the internet.

Follow the zen of python:
Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
Now is better than never.
Although never is often better than *right* now.
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!

Always try to provide useful code.

Consider a bug fixed ONLY IF you ran a test to check that it failed before and
passed after your fix.

Never trust yours intuition. Always double check.

Explicitly providing --source=. is an antipattern. Use DefaultPath instead.

Always start by running tests to have a baseline. Never try to add a feature if
the baseline is not totally green.

Never edit claude's memory.

Put stuff in CLAUDE.md ONLY IF the stuff makes sense for claude only. Most
of the time, the information will benefit a human reader and must be put in an
org file.

When things start drifting from our plan, don't take initiatives, propose a new
plan.

Fundamental rules of examples to never break:
1. ALL the example will be constructed from the readme.org, either by running a
   block or by tangling,
2. the commands shown in the example show EXACTLY what a user would use in a
   real life project (yet, we may wrap the command to ease mocking, taking
   shortcuts)
