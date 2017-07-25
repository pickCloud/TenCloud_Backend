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

# version
version=$4

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
        IMAGE_REGISTRY="${APP_NAME}:${version}"
        if docker build -t "${IMAGE_REGISTRY}" .;then
            log "image build successfull"
        else
            cp ${BASE_DIR}/config.json ~/.docker/config.json
            chmod 600 ~/.docker/config.json
            docker build -t "${IMAGE_REGISTRY}" .
        fi
    fi
}
image_push(){
    log "image push"
    new_tag="${REGISRTY}/${IMAGE_REGISTRY}"
    docker tag "${IMAGE_REGISTRY}" "${new_tag}"
    docker push "${new_tag}"
}
main(){

    if [ -f "${LOCK_FILE}" ];then
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
