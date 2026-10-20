pipeline {
  agent any
  options { disableConcurrentBuilds(); timeout(time: 90, unit: 'MINUTES') }
  stages {
    stage('Validate Docker VM and exact source') {
      steps {
        sh '''#!/bin/sh
set -eu
test "$(docker info --format '{{.Name}}')" = docker
test "$(git rev-parse --abbrev-ref HEAD)" != master
test -z "$(git status --porcelain)"
python3 -m py_compile ops/homelab/deploy.py
python3 -m unittest discover -s ops/homelab -p 'test_*.py' -v
test "$(docker info --format '{{.Architecture}}')" = x86_64
'''
      }
    }
    stage('Upstream tests and immutable image') {
      steps {
        sh '''#!/bin/sh
set -eu
sha=$(git rev-parse HEAD)
docker build -f ops/homelab/Dockerfile --build-arg VCS_REF="$sha" -t "local/jellyfin-homelab:$sha" .
id=$(docker create "local/jellyfin-homelab:$sha")
trap 'docker rm "$id" >/dev/null' EXIT
docker cp "$id:/homelab-test-results" test-results
test -n "$(find test-results -name '*.trx' -print -quit)"
docker run --rm --network none --entrypoint /usr/lib/jellyfin/bin/jellyfin "local/jellyfin-homelab:$sha" --version
'''
      }
    }
    stage('Back up and deploy Jellyfin only') {
      when { branch 'homelab' }
      steps {
        sh '''#!/bin/sh
set -eu
sha=$(git rev-parse HEAD)
docker run --rm -i --user 0:0 --network host --entrypoint python3 \
 -v /var/run/docker.sock:/var/run/docker.sock \
 -v /srv/homelab/stacks/media/yams:/srv/homelab/stacks/media/yams \
 -v /opt/yams/config/jellyfin:/opt/yams/config/jellyfin:ro \
 -v /srv/homelab/archive/jellyfin-ci:/srv/homelab/archive/jellyfin-ci \
 local/jenkins-controller:latest - "local/jellyfin-homelab:$sha" "$sha" < ops/homelab/deploy.py
'''
      }
    }
  }
  post { always { archiveArtifacts artifacts: 'test-results/**/*.trx', allowEmptyArchive: true } }
}
