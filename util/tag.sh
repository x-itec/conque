#!/bin/bash

# stupid, brute force tagging script
# e.g.:
#  ../util/tag.sh 2.3 2011-09-02 2011

prod_name=conque_$1

svn export https://conque.googlecode.com/svn/trunk $prod_name

find ./$prod_name/ -type f | xargs sed -i "s#__VERSION__#$1#"
find ./$prod_name/ -type f | xargs sed -i "s#__MODIFIED__#$2#"
find ./$prod_name/ -type f | xargs sed -i "s#__YEAR__#$3#"

sed -i 's#^.*logging.*$##' $prod_name/autoload/conque_term.vim $prod_name/autoload/conque_term/*
sed -i 's#^.*debug.*$##i' $prod_name/autoload/conque_term.vim $prod_name/autoload/conque_term/*
sed -i 's#^.*LOG_FILENAME.*$##' $prod_name/autoload/conque_term.vim $prod_name/autoload/conque_term/*

rm -r $prod_name/tests

tar -cvf $prod_name.tar $prod_name
gzip $prod_name.tar
mv $prod_name.tar.gz ../downloads/

pushd $prod_name
zip -r $prod_name.zip *
popd
mv $prod_name/$prod_name.zip ../downloads/

