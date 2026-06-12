import os
import re
import json
import hashlib
from base64 import b64decode
from io import BytesIO
from pathlib import PurePosixPath
from urllib.parse import urlparse
from zipfile import ZipFile

import httpx
import yaml

from app.config.setting import settings
from app.core.exceptions import CustomException

from .base import MarketAdapter, MarketAdapterItem, MarketInstallPackage


class GitHubRepoMarketAdapter(MarketAdapter):
    """GitHub 仓库型 Skill 市场适配器"""

    def __init__(self, base_url: str, branch: str | None = None, config: dict | None = None) -> None:
        super().__init__(base_url=base_url, branch=branch, config=config)
        self.owner, self.repo = self._parse_repo_url(base_url)
        self.branch = branch or self.config.get("branch") or "main"
        self.timeout = float(self.config.get("timeout", 20))
        self.max_items = int(self.config.get("max_items", 200))
        self.max_install_files = int(self.config.get("max_install_files", 80))
        self.manifest_paths = self.config.get("manifest_paths") or [
            ".claude-plugin/marketplace.json",
            ".codex-plugin/plugin.json",
            "marketplace.json",
        ]
        self.discover_mode = str(self.config.get("discover_mode") or "auto")
        self.include_manifest_skills = bool(self.config.get("include_manifest_skills", False))
        token = self.config.get("token")
        self.headers = {"Accept": "application/vnd.github+json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        self.github_proxy_prefix = (
            self.config.get("github_proxy_prefix")
            or os.getenv("SKILL_MARKET_GITHUB_PROXY_PREFIX")
            or settings.SKILL_MARKET_GITHUB_PROXY_PREFIX
        )

    async def list_items(self, limit: int | None = None) -> list[MarketAdapterItem]:
        tree = await self._get_tree()
        item_limit = limit or self.max_items
        manifest_items = await self._list_manifest_items(tree=tree, limit=item_limit)
        if manifest_items and not self.include_manifest_skills:
            return manifest_items[:item_limit]
        if manifest_items and self.include_manifest_skills:
            item_limit = max(item_limit - len(manifest_items), 0)

        skill_paths = [
            entry["path"]
            for entry in tree
            if entry.get("type") == "blob" and PurePosixPath(entry.get("path", "")).name == "SKILL.md"
        ][:item_limit]
        items: list[MarketAdapterItem] = []
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers=self.headers,
            trust_env=False,
        ) as client:
            for skill_md_path in skill_paths:
                skill_md = await self._fetch_raw(client, skill_md_path)
                meta = self._parse_frontmatter(skill_md)
                skill_dir = str(PurePosixPath(skill_md_path).parent)
                skill_dir = "" if skill_dir == "." else skill_dir
                readme_path = self._find_readme(tree, skill_dir)
                name = str(meta.get("name") or PurePosixPath(skill_dir).name or self.repo)
                description = meta.get("description")
                title = str(meta.get("title") or meta.get("display_name") or name)
                item = MarketAdapterItem(
                    external_id=skill_dir or name,
                    name=self._normalize_name(name),
                    title=title,
                    description=str(description) if description else None,
                    category=self._first_str(meta.get("category")),
                    tags=self._normalize_tags(meta.get("tags")),
                    version=self._first_str(meta.get("version")),
                    author=self._first_str(meta.get("author")),
                    license=self._first_str(meta.get("license")),
                    homepage_url=self._first_str(meta.get("homepage") or meta.get("homepage_url")),
                    repository_url=self.base_url,
                    skill_path=skill_dir,
                    skill_md_url=self._raw_url(skill_md_path),
                    readme_url=self._raw_url(readme_path) if readme_path else None,
                    market_kind="skill",
                    skill_paths=[skill_dir] if skill_dir else [""],
                    source_branch=self.branch,
                    source_commit=self.config.get("commit_sha"),
                    content_hash=self._content_hash(skill_md),
                    file_count=self._count_files(tree, skill_dir),
                    package_size=0,
                    raw_meta=meta,
                )
                items.append(item)
        return [*manifest_items, *items][: limit or self.max_items]

    async def get_install_package(self, item: MarketAdapterItem) -> MarketInstallPackage:
        if item.market_kind == "plugin":
            raise CustomException(msg="插件包需要逐个 Skill 安装，不能作为单个 Skill 包读取")
        tree = await self._get_tree()
        root = item.skill_path.strip("/")
        prefix = f"{root}/" if root else ""
        files = [
            entry
            for entry in tree
            if entry.get("type") == "blob" and str(entry.get("path", "")).startswith(prefix)
        ][: self.max_install_files]
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers=self.headers,
            trust_env=False,
        ) as client:
            skill_md = await self._fetch_raw(client, f"{prefix}SKILL.md")
            readme_path = self._find_readme(tree, root)
            readme = await self._fetch_raw(client, readme_path) if readme_path else None
            package_files: list[dict] = []
            for entry in files:
                path = str(entry.get("path"))
                rel_path = path[len(prefix) :] if prefix else path
                if rel_path in {"SKILL.md", "README.md", "README.MD", "readme.md"}:
                    continue
                content = await self._fetch_raw(client, path)
                package_files.append(
                    {
                        "path": rel_path,
                        "type": "file",
                        "content": content,
                        "content_type": self._content_type(rel_path),
                        "description": None,
                        "status": "0",
                    }
                )
        return MarketInstallPackage(skill_md=skill_md, readme=readme, files=package_files)

    async def list_plugin_skill_items(self, item: MarketAdapterItem) -> list[MarketAdapterItem]:
        """把插件包条目展开为可安装的单个 Skill 条目。"""

        if item.market_kind != "plugin":
            return [item]
        tree = await self._get_tree()
        skill_paths = item.skill_paths or item.raw_meta.get("skill_paths") or []
        items: list[MarketAdapterItem] = []
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers=self.headers,
            trust_env=False,
        ) as client:
            for skill_dir in skill_paths:
                skill_dir = str(skill_dir).strip().strip("/")
                skill_md_path = f"{skill_dir}/SKILL.md" if skill_dir else "SKILL.md"
                skill_md = await self._fetch_raw(client, skill_md_path)
                meta = self._parse_frontmatter(skill_md)
                readme_path = self._find_readme(tree, skill_dir)
                name = str(meta.get("name") or PurePosixPath(skill_dir).name or self.repo)
                description = meta.get("description")
                items.append(
                    MarketAdapterItem(
                        external_id=f"{item.external_id}:{skill_dir}",
                        name=self._normalize_name(name),
                        title=str(meta.get("title") or meta.get("display_name") or name),
                        description=str(description) if description else None,
                        category=self._first_str(meta.get("category")),
                        tags=self._normalize_tags(meta.get("tags")),
                        version=self._first_str(meta.get("version")),
                        author=self._first_str(meta.get("author")),
                        license=self._first_str(meta.get("license")),
                        homepage_url=self._first_str(meta.get("homepage") or meta.get("homepage_url")),
                        repository_url=self.base_url,
                        skill_path=skill_dir,
                        skill_md_url=self._raw_url(skill_md_path),
                        readme_url=self._raw_url(readme_path) if readme_path else None,
                        market_kind="skill",
                        plugin_name=item.plugin_name,
                        plugin_description=item.plugin_description,
                        skill_paths=[skill_dir],
                        source_branch=self.branch,
                        source_commit=item.source_commit,
                        content_hash=self._content_hash(skill_md),
                        file_count=self._count_files(tree, skill_dir),
                        package_size=0,
                        raw_meta={**meta, "plugin_name": item.plugin_name},
                    )
                )
        return items

    async def _get_tree(self) -> list[dict]:
        branches = [self.branch]
        if self.branch != "master":
            branches.append("master")
        last_error = ""
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers=self.headers,
            trust_env=False,
        ) as client:
            for branch in branches:
                url = self._proxy_url(
                    f"https://api.github.com/repos/{self.owner}/{self.repo}/git/trees/{branch}?recursive=1"
                )
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    self.branch = branch
                    self.config["commit_sha"] = data.get("sha")
                    return data.get("tree", [])
                last_error = f"{response.status_code} {response.text[:200]}"
                archive_tree = await self._get_tree_from_archive(client, branch)
                if archive_tree:
                    self.branch = branch
                    return archive_tree
        raise CustomException(msg=f"读取 GitHub 仓库目录失败: {last_error}")

    async def _list_manifest_items(self, tree: list[dict], limit: int) -> list[MarketAdapterItem]:
        if self.discover_mode == "scan":
            return []
        manifest_path = self._find_manifest(tree)
        if not manifest_path:
            return []
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers=self.headers,
            trust_env=False,
        ) as client:
            content = await self._fetch_raw(client, manifest_path)
        try:
            manifest = json.loads(content)
        except json.JSONDecodeError as exc:
            raise CustomException(msg=f"市场清单 JSON 解析失败: {manifest_path}: {exc}") from exc

        plugins = manifest.get("plugins") if isinstance(manifest, dict) else None
        if not isinstance(plugins, list):
            return []

        metadata = manifest.get("metadata") if isinstance(manifest.get("metadata"), dict) else {}
        owner = manifest.get("owner") if isinstance(manifest.get("owner"), dict) else {}
        items: list[MarketAdapterItem] = []
        for plugin in plugins[:limit]:
            if not isinstance(plugin, dict):
                continue
            skill_paths = self._normalize_skill_paths(plugin.get("skills"))
            if not skill_paths:
                continue
            name = self._normalize_name(str(plugin.get("name") or PurePosixPath(skill_paths[0]).name))
            description = plugin.get("description") or metadata.get("description")
            item = MarketAdapterItem(
                external_id=f"plugin:{name}",
                name=name,
                title=str(plugin.get("title") or plugin.get("name") or name),
                description=str(description) if description else None,
                category=self._first_str(plugin.get("category")),
                tags=self._normalize_tags(plugin.get("tags")),
                version=self._first_str(plugin.get("version") or metadata.get("version")),
                author=self._first_str(plugin.get("author") or owner.get("name")),
                license=self._first_str(plugin.get("license")),
                homepage_url=self._first_str(plugin.get("homepage") or plugin.get("homepage_url")),
                repository_url=self.base_url,
                skill_path=str(plugin.get("source") or "./"),
                skill_md_url=None,
                readme_url=None,
                market_kind="plugin",
                plugin_name=name,
                plugin_description=str(description) if description else None,
                skill_paths=skill_paths,
                source_branch=self.branch,
                source_commit=self.config.get("commit_sha"),
                content_hash=self._content_hash(json.dumps(plugin, sort_keys=True, ensure_ascii=False)),
                file_count=sum(self._count_files(tree, path) for path in skill_paths),
                package_size=0,
                raw_meta={
                    "manifest_path": manifest_path,
                    "marketplace": {
                        "name": manifest.get("name"),
                        "owner": owner,
                        "metadata": metadata,
                    },
                    "plugin": plugin,
                    "skill_paths": skill_paths,
                },
            )
            items.append(item)
        return items

    async def _fetch_raw(self, client: httpx.AsyncClient, path: str) -> str:
        url = self._proxy_url(f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{path}")
        response = await client.get(url, params={"ref": self.branch})
        if response.status_code < 400:
            data = response.json()
            content = data.get("content")
            if not content:
                return ""
            return b64decode(str(content)).decode("utf-8", errors="replace")

        raw_response = await client.get(self._proxy_url(self._raw_url(path)))
        if raw_response.status_code >= 400:
            raise CustomException(msg=f"读取远端文件失败: {path}")
        return raw_response.content.decode("utf-8", errors="replace")

    async def _get_tree_from_archive(self, client: httpx.AsyncClient, branch: str) -> list[dict]:
        url = self._proxy_url(f"https://codeload.github.com/{self.owner}/{self.repo}/zip/refs/heads/{branch}")
        response = await client.get(url)
        if response.status_code >= 400:
            return []
        tree: list[dict] = []
        with ZipFile(BytesIO(response.content)) as archive:
            for name in archive.namelist():
                if name.endswith("/"):
                    continue
                parts = PurePosixPath(name).parts
                if len(parts) <= 1:
                    continue
                tree.append({"path": str(PurePosixPath(*parts[1:])), "type": "blob"})
        return tree

    def _raw_url(self, path: str) -> str:
        return f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/{self.branch}/{path}"

    def _proxy_url(self, url: str) -> str:
        prefix = str(self.github_proxy_prefix or "").strip()
        if not prefix:
            return url
        return f"{prefix.rstrip('/')}/{url}"

    @staticmethod
    def _parse_repo_url(url: str) -> tuple[str, str]:
        parsed = urlparse(url.strip())
        parts = [part for part in parsed.path.strip("/").split("/") if part]
        if parsed.netloc not in {"github.com", "www.github.com"} or len(parts) < 2:
            raise CustomException(msg="GitHub 市场地址必须形如 https://github.com/owner/repo")
        return parts[0], parts[1].removesuffix(".git")

    @staticmethod
    def _parse_frontmatter(content: str) -> dict:
        if not content.lstrip().startswith("---"):
            return {}
        match = re.match(r"^\s*---\s*\n(.*?)\n---\s*", content, re.S)
        if not match:
            return {}
        data = yaml.safe_load(match.group(1)) or {}
        return data if isinstance(data, dict) else {}

    def _find_manifest(self, tree: list[dict]) -> str | None:
        paths = {
            str(path).strip().strip("/")
            for path in self.manifest_paths
            if str(path).strip()
        }
        for entry in tree:
            path = str(entry.get("path", ""))
            if entry.get("type") == "blob" and path in paths:
                return path
        return None

    @staticmethod
    def _find_readme(tree: list[dict], skill_dir: str) -> str | None:
        prefix = f"{skill_dir.strip('/')}/" if skill_dir else ""
        names = {f"{prefix}README.md", f"{prefix}README.MD", f"{prefix}readme.md"}
        for entry in tree:
            path = str(entry.get("path", ""))
            if entry.get("type") == "blob" and path in names:
                return path
        return None

    @staticmethod
    def _normalize_skill_paths(value) -> list[str]:
        if not isinstance(value, list):
            return []
        paths: list[str] = []
        for item in value:
            path = str(item).strip().strip("/")
            if path.startswith("./"):
                path = path[2:]
            if path and ".." not in PurePosixPath(path).parts:
                paths.append(path)
        return paths

    @staticmethod
    def _count_files(tree: list[dict], skill_dir: str) -> int:
        prefix = f"{skill_dir.strip('/')}/" if skill_dir else ""
        return sum(
            1
            for entry in tree
            if entry.get("type") == "blob" and str(entry.get("path", "")).startswith(prefix)
        )

    @staticmethod
    def _content_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()

    @staticmethod
    def _normalize_name(value: str) -> str:
        name = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-_")
        return name[:100] or "external-skill"

    @staticmethod
    def _normalize_tags(value) -> list[str] | None:
        if not value:
            return None
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return [item.strip() for item in str(value).split(",") if item.strip()]

    @staticmethod
    def _first_str(value) -> str | None:
        if value is None:
            return None
        if isinstance(value, list):
            return str(value[0]) if value else None
        return str(value)

    @staticmethod
    def _content_type(path: str) -> str:
        suffix = PurePosixPath(path).suffix.lower()
        if suffix in {".md", ".markdown"}:
            return "markdown"
        if suffix == ".py":
            return "python"
        if suffix in {".sh", ".bash", ".zsh"}:
            return "shell"
        if suffix == ".json":
            return "json"
        return "text"
