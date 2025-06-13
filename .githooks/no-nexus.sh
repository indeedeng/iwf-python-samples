#! /usr/bin/env bash

gsed -i'' \
    -e '/./{H;$!d}' \
    -e 'x' \
    -e 's|\[package.source\]\ntype\s*=\s*\"legacy\"\nurl\s*=\s*\"https://nexus.corp.indeed.com/repository/pypi/simple\"\nreference\s*=\s*\"nexus\"||' \
    poetry.lock

gsed -i'' \
    -e '1{/^\s*$/d}' \
    poetry.lock

gsed -i'' \
    -e '/^\s*$/N;/^\s*\n$/D' \
    poetry.lock

CHANGES=$(git diff --exit-code poetry.lock | grep -Pzo '\-\[package.source\]\n\-type = "legacy"\n\-url = "https://nexus.corp.indeed.com/repository/pypi/simple"\n\-reference = "nexus"\n' | wc -c)

if [[ $CHANGES -eq 0 ]]; then
  exit 0
fi

exit 1
