import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, List, Optional, Dict, Any

import httpx

from dto import git_file_dto
from utils import const

http_client_error = RuntimeError("Http client is not initialized")


class GitHubClient:
    """
    GitHub client
    """

    def __init__(
        self,
        repo: str,
        repo_owner: str,
        token: str,
        branch: Optional[str] = None,
    ) -> None:
        """
        Init variables
        :param repo: repo name
        :param token: github token
        :param branch: repo branch
        """

        self.repo = repo
        self.branch = branch
        self.token = token
        self.url = f"https://api.github.com/repos/{repo_owner}/{repo}/contents"
        self._client: Optional[httpx.AsyncClient] = None

    @asynccontextmanager
    async def __call__(self):
        """
        Init http client
        """

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Client/1.0",
            "Authorization": f"token {self.token}"
        }

        async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
            self._client = client
            yield self
            self._client = None

    async def _get(self, url: str, params: Optional[Dict] = None) -> Any:
        if not self._client:
            raise http_client_error

        response = await self._client.get(url, params=params)
        response.raise_for_status()

        return response.json()

    async def _download_content(self, url: str) -> Optional[str]:
        """
        Download file content
        :param url: file url
        :return: file content
        """

        if not self._client:
            raise http_client_error

        try:
            response = await self._client.get(url)

            if response.status_code == 200:
                return response.text

            return None
        except Exception as e:
            print(f"Error while downloading content from {url}: {e}")

            return None

    async def _process_file(self, file_info: Dict) -> Optional[git_file_dto.GitFile]:
        """
        Load file metadata and content
        :param file_info: file data
        :return: file content
        """

        try:
            if file_info.get("type") != "file":
                return None

            path = file_info["path"]
            ext = Path(path).suffix.lower()

            file_type = (
                const.FileType.CODE
                if ext.lower() in const.code_extensions
                else const.FileType.DOC
            ) if ext else const.FileType.UNKNOWN

            content = None
            download_url = file_info.get("download_url")

            if download_url:
                content = await self._download_content(download_url)

            if content is None:
                return None

            return git_file_dto.GitFile(
                path=path,
                sha=file_info["sha"],
                size=file_info.get("size", 0),
                type=file_type,
                content=content
            )

        except Exception as e:
            print(f"Error while processing file {file_info.get('path', 'unknown')}: {e}")

            return None

    async def _collect_files_metadata(self, items: List[Dict]) -> list[Dict]:
        """
        Get files metadata
        :param items: files retrieval data
        :return: files metadata
        """

        result: List[Dict] = []

        for item in items:
            if item["type"] == "file":
                result.append(item)
            elif item["type"] == "dir":
                dir_url = f"{self.url}/{item['path']}"
                params = {"ref": self.branch} if self.branch else None

                try:
                    dir_items = await self._get(dir_url, params)

                    if isinstance(dir_items, list):
                        subdir_files = await self._collect_files_metadata(dir_items)
                        result.extend(subdir_files)

                except Exception as e:
                    print(f"Error while traversing directory {item['path']}: {e}")

        return result

    async def get_files_batch(
        self,
        batch_size: int = 10,
    ) -> AsyncGenerator[List[git_file_dto.GitFile], None]:
        """
        Get files from repository by batch
        :param batch_size: batch size
        :return: files batch
        """

        params = {"ref": self.branch} if self.branch else None
        items = await self._get(self.url, params)

        if not isinstance(items, list):
            items = [items]

        all_files = await self._collect_files_metadata(items)

        for i in range(0, len(all_files), batch_size):
            batch = all_files[i:i + batch_size]

            tasks = [self._process_file(file_info) for file_info in batch]
            results = await asyncio.gather(*tasks)

            valid_files = [r for r in results if r is not None]

            if valid_files:
                yield valid_files

            if i + batch_size < len(all_files):
                await asyncio.sleep(0.5)
