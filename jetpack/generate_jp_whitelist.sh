#!/bin/bash

rm ../validator/testcases/jetpack_data.txt

cd addon-sdk
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

sort ../../validator/testcases/jetpack_data.txt -d -o ../../validator/testcases/jetpack_data.txt

# Delete the old pickle file.
rm ../../validator/testcases/jetpack/jetpack_data.txt.pickle
# This will generate the new pickle file.
cd .. && nosetests
