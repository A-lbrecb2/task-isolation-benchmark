#!/usr/bin/env bash
# Runs the headless Karma test suite of one project: ./test.sh full-repo | ./test.sh slices/T3-footer
set -e
if [ -z "$1" ]; then echo "usage: $0 <project folder>"; exit 1; fi
cd "$(dirname "$0")/$1"
npx ng test --watch=false --karma-config karma.headless.js
