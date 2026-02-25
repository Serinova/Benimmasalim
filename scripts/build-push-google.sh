#!/usr/bin/env bash
# BenimMasalim - Backend + Frontend Docker build ve Google Artifact Registry'ye push
#
# Yontem 1 - Cloud Build (Google sunucuda build, otomatik push):
#   ./scripts/build-push-google.sh --cloud-build
#
# Yontem 2 - Yerel Docker build + push:
#   ./scripts/build-push-google.sh
#   (Once: gcloud auth configure-docker europe-west1-docker.pkg.dev)

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REGION="${REGION:-europe-west1}"
REPO="${REPO:-benimmasalim}"
TAG="${TAG:-latest}"

usage() {
  echo "Usage: $0 [--cloud-build] [--project ID] [--region R] [--repo R] [--tag T]"
  echo "  --cloud-build  Use Cloud Build (build on Google)"
  echo "  --project ID   GCP project (default: gcloud config)"
  echo "  --region R     Artifact Registry region (default: europe-west1)"
  echo "  --repo R       Repository name (default: benimmasalim)"
  echo "  --tag T        Image tag (default: latest)"
  exit 0
}

CLOUD_BUILD=false
PROJECT_ID=""
while [ $# -gt 0 ]; do
  case "$1" in
    --cloud-build) CLOUD_BUILD=true ;;
    --project)     PROJECT_ID="$2"; shift ;;
    --region)      REGION="$2"; shift ;;
    --repo)        REPO="$2"; shift ;;
    --tag)         TAG="$2"; shift ;;
    -h|--help)     usage ;;
  esac
  shift
done

if [ -z "$PROJECT_ID" ]; then
  PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
  [ -z "$PROJECT_ID" ] && { echo "PROJECT_ID gerekli: --project XXX veya gcloud config set project XXX"; exit 1; }
fi

FULL_REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}"

if [ "$CLOUD_BUILD" = true ]; then
  echo "Cloud Build ile build + push..."
  (cd "$ROOT" && gcloud builds submit \
    --config=cloudbuild.yaml \
    --substitutions="_REGION=${REGION},_REPO=${REPO},_TAG=${TAG}" \
    --project="$PROJECT_ID" \
    .)
  echo "Bitti. Image'lar Artifact Registry'de."
  exit 0
fi

echo "Yerel Docker build + push (registry: $FULL_REGISTRY)"
echo "Docker login: gcloud auth configure-docker ${REGION}-docker.pkg.dev"

# Backend
cd "$ROOT/backend"
docker build -t "${FULL_REGISTRY}/backend:${TAG}" .
docker push "${FULL_REGISTRY}/backend:${TAG}"

# Frontend
cd "$ROOT/frontend"
docker build --target runner -t "${FULL_REGISTRY}/frontend:${TAG}" .
docker push "${FULL_REGISTRY}/frontend:${TAG}"

echo "Bitti. backend:${TAG} ve frontend:${TAG} push edildi."
