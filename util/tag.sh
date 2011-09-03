#!/bin/bash

# stupid, brute force tagging script
# e.g.:
#  ./tag.sh 2.3 2011-09-02 2011

svn export https://conque.googlecode.com/svn/trunk conque_$1

find ./conque_$1/ -type f | xargs sed -i "s#__VERSION__#$1#"
find ./conque_$1/ -type f | xargs sed -i "s#__MODIFIED__#$2#"
find ./conque_$1/ -type f | xargs sed -i "s#__YEAR__#$3#"

sed -i 's#^.*logging.*$##' conque_$1/autoload/conque_term.vim conque_$1/autoload/conque_term/*
sed -i 's#^.*debug.*$##' conque_$1/autoload/conque_term.vim conque_$1/autoload/conque_term/*
sed -i 's#^.*LOG_FILENAME.*$##' conque_$1/autoload/conque_term.vim conque_$1/autoload/conque_term/*

rm -r conque_$1/tests

