#!/bin/sh

branch="dev_hongguoan"
current_branch=$(git branch 2>/dev/null | grep "^\*" | sed -e "s/^\*\ //")
if [ ${current_branch} != ${branch} ];then
    git checkout "${branch}"
    echo "checkout to dev_hongguoan"
fi
echo "current branch is dev_hongguoan"
