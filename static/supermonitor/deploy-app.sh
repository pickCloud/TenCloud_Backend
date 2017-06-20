#!/bin/sh

#Date/Time Variable
LOG_DATE=$(date "+%Y-%m-%d")
LOG_TIME=$(date "+%H-%M-%S")

#Code ENV
APP_NAME="demo"
BASE_DIR="$HOME/deploy"
CODE_DIR="${BASE_DIR}/code/${APP_NAME}"
CODE_URL="git@github.com:lanarthur/test.git"
LOCK_FILE="/tmp/deploy.lock"

#Shell env
SHELL_NAME="deploy-app.sh"
SHELL_LOG="${BASE_DIR}/log/${SHELL_NAME}.log"

# Docker
IMAGE_REGISTRY=""
REGISRTY="www.jmkbio.com/library"

log(){
    log_info=$1
    echo "${LOG_DATE}${LOG_TIME}: ${log_info} " >> ${SHELL_LOG}
}
shell_lock(){
    touch ${LOCK_FILE}
}
shell_unlock(){
    rm -f ${LOCK_FILE}
}
code_get(){
    log "code_get";
    if [ ! -d ${CODE_DIR} ];then
      mkdir -p ${CODE_DIR}
    fi
    if ls -A ${CODE_DIR} &> /dev/null;then
      git clone ${CODE_URL} ${CODE_DIR}
    else
      cd ${CODE_DIR}
      git pull
    fi
}
code_build(){
    branch=$1
    log "code_build"
    cd ${CODE_DIR} || exist 1
    if git checkout $branch &> /dev/null;then
        ver=$(git rev-parse --short HEAD)
        $IMAGE_REGISTRY="${APP_NAME}:${branch}-${ver}"
        #docker build -t ${APP_NAME}:${IMAGE_TAG} .
        docker build -t ${IMAGE_REGISTRY} .
    fi
}
image_push(){
    log "image push"
    new_tag="${REGISRTY}/${IMAGE_REGISTRY}"
    docker tag ${IMAGE_REGISTRY} ${new_tag}
    docker push ${new_tag}
}
main(){

    if [ -f ${LOCK_FILE} ];then
	    echo "Deploy is running" && exit;
    fi
    if [ ! -d ${CODE_DIR} ];then
        mkdir -p ${BASE_DIR}/log
    fi

	  shell_lock;
	  code_get;
	  code_build $1;
    image_push;
	  shell_unlock;
}

main $1
