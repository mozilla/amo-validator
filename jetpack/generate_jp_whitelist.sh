#!/bin/bash

rm ../validator/testcases/jetpack_data.txt
rm ../validator/testcases/jetpack_data.txt.pickle

pushd jpm
git fetch --tags
for tagname in `git tag`;
do
    # Check out the tag.
    git checkout $tagname

    # Hash the bootstrap.js file.
    python ../make_hash.py ./data/bootstrap.js $tagname >> ../../validator/testcases/jetpack_data.txt
done
popd

pushd addon-sdk
git pull origin --tags
for tagname in `git tag`;
do
    # Check out the tag.
    git checkout $tagname

    # Hash all of the JS files.
    for f in `find . -type f -name "*.js"`;
    do
        python ../make_hash.py $f $tagname >> ../../validator/testcases/jetpack_data.txt
    done

    # Run again for HTML, because it gets bundled, too.
    for f in `find . -type f -name "*.html"`;
    do
        python ../make_hash.py $f $tagname >> ../../validator/testcases/jetpack_data.txt
    done
done
popd

sort ../validator/testcases/jetpack_data.txt -d -o ../validator/testcases/jetpack_data.txt
# This will generate the new pickle file.
cd .. && nosetests
