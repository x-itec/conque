#!/bin/bash

# stupid, brute force tagging script

mkdir tags/$1
mkdir tags/$1/autoload
mkdir tags/$1/plugin
mkdir tags/$1/syntax
mkdir tags/$1/doc

cp trunk/autoload/conque_term.vim tags/$1/autoload/
cp trunk/plugin/conque_term.vim tags/$1/plugin/
cp trunk/syntax/conque_term.vim tags/$1/syntax/
cp trunk/doc/conque_term.txt tags/$1/doc/

find ./tags/$1/ -type f | xargs sed -i "s#__VERSION__#$2#"
find ./tags/$1/ -type f | xargs sed -i "s#__MODIFIED__#$3#"

