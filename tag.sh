#!/bin/bash

# stupid, brute force tagging script

mkdir tags/$1
mkdir tags/$1/autoload
mkdir tags/$1/autoload/subprocess
mkdir tags/$1/plugin
mkdir tags/$1/syntax

cp trunk/conque/autoload/conque.vim tags/$1/autoload/
cp trunk/conque/plugin/conque.vim tags/$1/plugin/
cp trunk/conque/syntax/conque.vim tags/$1/syntax/
cp trunk/subprocess/autoload/subprocess.vim tags/$1/autoload/
cp trunk/subprocess/autoload/subprocess/proc_py.vim tags/$1/autoload/subprocess/
cp trunk/subprocess/autoload/subprocess/shell_translate.vim tags/$1/autoload/subprocess/
cp trunk/conque/README tags/$1/
cp trunk/conque/license.txt tags/$1/

find ./tags/$1/ -type f | xargs sed -i "s#__VERSION__#$2#"
find ./tags/$1/ -type f | xargs sed -i "s#__MODIFIED__#$3#"
find ./tags/$1/ -type f | xargs sed -i 's#^.*s:log.*$##'

