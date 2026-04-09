Use those scripts only:
- ./run.sh
- ./yamldagger.sh
- ./tangle.sh
- ./test.sh

Use ./tangle-nodagger.sh ONLY IF you need to resolve the chicken-and-egg
problem.

Don't piss code. Always plan.

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
