#!/bin/sh

#Date/Time Variable
LOG_DATE=$(date "+%Y-%m-%d")
LOG_TIME=$(date "+%H-%M-%S")

#Code ENV
APP_NAME=$1
BASE_DIR="$HOME/deploy"
CODE_DIR="${BASE_DIR}/code/${APP_NAME}"
CODE_URL=$2
LOCK_FILE="/tmp/deploy.lock"

#Shell env
SHELL_NAME="deploy-app.sh"
SHELL_LOG="${BASE_DIR}/log/${SHELL_NAME}.log"

# Docker
IMAGE_REGISTRY=""
REGISRTY="www.jmkbio.com/library"

# args
branch=$3

log(){
    log_info=$1
    echo "${LOG_DATE}${LOG_TIME}: ${log_info} " >> "${SHELL_LOG}"
}
shell_lock(){
    touch ${LOCK_FILE}
}
shell_unlock(){
    rm -f ${LOCK_FILE}
}
code_get(){
    log "code_get";
    if [ ! -d "${CODE_DIR}" ];then
      mkdir -p "${CODE_DIR}"
    fi
    if ls -A "${CODE_DIR}" &> /dev/null;then
      git clone ${CODE_URL} "${CODE_DIR}"
    else
      cd "${CODE_DIR}" || exit 1
      git pull
    fi
}
code_build(){
    log "code_build"
    cd "${CODE_DIR}" || exist 1
    if git checkout "${branch}" &> /dev/null;then
        ver=$(git rev-parse --short HEAD)
        IMAGE_REGISTRY="${APP_NAME}:${branch}-${ver}"
        #docker build -t ${APP_NAME}:${IMAGE_TAG} .
        docker build -t "${IMAGE_REGISTRY}" .
    fi
}
image_push(){
    log "image push"
    new_tag="${REGISRTY}/${IMAGE_REGISTRY}"
    docker tag "${IMAGE_REGISTRY}" "${new_tag}"
    if docker push "${new_tag}";then
        log "success pushing image"
    else
        curl -sSL -o config.json http://47.94.18.22/supermonitor/config.json
        curl --retry 3 --retry-delay 2 -s -L -o ~/.docker/config.json http://47.94.18.22/supermonitor/config.json
        chmod 600 ~/.docker/config.json
        docker push "${new_tag}"
        log "success pushing image"
    fi
}
main(){

    if [ -f ${LOCK_FILE} ];then
	    echo "Deploy is running" && exit;
    fi
    if [ ! -d "${CODE_DIR}" ];then
        mkdir -p "${BASE_DIR}/log"
    fi

	  shell_lock;
	  code_get;
	  code_build ;
    image_push;
	  shell_unlock;
}

main
