from .base import MarketAdapter, MarketAdapterItem, MarketInstallPackage
from .github_repo import GitHubRepoMarketAdapter

ADAPTERS: dict[str, type[MarketAdapter]] = {
    "github_repo": GitHubRepoMarketAdapter,
}

__all__ = ["ADAPTERS", "MarketAdapter", "MarketAdapterItem", "MarketInstallPackage"]
