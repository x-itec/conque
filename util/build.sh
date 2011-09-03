#!/bin/bash


sed -i 's#^.*logging.*$##' autoload/conque_term.vim
sed -i 's#^.*debug.*$##' autoload/conque_term.vim
sed -i 's#^.*LOG_FILENAME.*$##' autoload/conque_term.vim

rm -r tests

