#!/usr/bin/env bash
set -euo pipefail

UPSTREAM_REMOTE="${UPSTREAM_REMOTE:-upstream}"
ORIGIN_REMOTE="${ORIGIN_REMOTE:-origin}"
UPSTREAM_BRANCH="${UPSTREAM_BRANCH:-master}"
MIRROR_BRANCH="${MIRROR_BRANCH:-upstream-main}"

echo "准备同步官方分支：${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH} -> ${MIRROR_BRANCH}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "错误：当前目录不是 Git 仓库。"
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "错误：当前工作区存在未提交改动，请先提交或暂存后再同步。"
  git status --short
  exit 1
fi

if ! git remote get-url "${UPSTREAM_REMOTE}" >/dev/null 2>&1; then
  echo "错误：未找到上游远程 ${UPSTREAM_REMOTE}。"
  exit 1
fi

if ! git remote get-url "${ORIGIN_REMOTE}" >/dev/null 2>&1; then
  echo "错误：未找到你的 fork 远程 ${ORIGIN_REMOTE}。"
  exit 1
fi

git fetch "${UPSTREAM_REMOTE}"

if ! git show-ref --verify --quiet "refs/remotes/${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}"; then
  echo "错误：未找到 ${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}。"
  exit 1
fi

git checkout "${MIRROR_BRANCH}"
git reset --hard "${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}"
git push "${ORIGIN_REMOTE}" "${MIRROR_BRANCH}" --force

echo "同步完成：${MIRROR_BRANCH} 已对齐 ${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}"
