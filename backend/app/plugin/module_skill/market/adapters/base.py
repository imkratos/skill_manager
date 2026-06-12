from dataclasses import dataclass, field


@dataclass
class MarketAdapterItem:
    """第三方市场条目的统一数据结构"""

    external_id: str
    name: str
    title: str
    description: str | None
    category: str | None
    tags: list[str] | None
    version: str | None
    author: str | None
    license: str | None
    homepage_url: str | None
    repository_url: str | None
    skill_path: str
    skill_md_url: str | None
    readme_url: str | None
    market_kind: str = "skill"
    plugin_name: str | None = None
    plugin_description: str | None = None
    skill_paths: list[str] = field(default_factory=list)
    source_branch: str | None = None
    source_commit: str | None = None
    content_hash: str | None = None
    file_count: int = 0
    package_size: int = 0
    raw_meta: dict = field(default_factory=dict)


@dataclass
class MarketInstallPackage:
    """安装到本地 Skill 管理模块所需的标准包"""

    skill_md: str
    readme: str | None
    files: list[dict]


class MarketAdapter:
    """第三方 Skill 平台适配器基类"""

    def __init__(self, base_url: str, branch: str | None = None, config: dict | None = None) -> None:
        self.base_url = base_url
        self.branch = branch
        self.config = config or {}

    async def list_items(self, limit: int | None = None) -> list[MarketAdapterItem]:
        raise NotImplementedError

    async def get_install_package(self, item: MarketAdapterItem) -> MarketInstallPackage:
        raise NotImplementedError

    async def list_plugin_skill_items(self, item: MarketAdapterItem) -> list[MarketAdapterItem]:
        raise NotImplementedError
