"""pytest 配置与共享 fixtures."""

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

from qqmusic_api import Client, Credential
from qqmusic_api.core.exceptions import CredentialExpiredError, CredentialInvalidError, NetworkError, RatelimitedError

TEST_CREDENTIAL_ENV_PREFIX = "QQMUSIC_"

TEST_DEVICE_CACHE_DIR = "qqmusic_api"
TEST_DEVICE_FILENAME = "device.json"


def _build_credential() -> Credential:
    """从测试环境变量构造凭证."""
    env_map = {
        "musicid": "MUSICID",
        "musickey": "MUSICKEY",
        "encrypt_uin": "ENCRYPT_UIN",
        "str_musicid": "STR_MUSICID",
        "login_type": "LOGIN_TYPE",
    }
    data = {
        field_name: value
        for field_name, env_name in env_map.items()
        if (value := os.getenv(f"{TEST_CREDENTIAL_ENV_PREFIX}{env_name}")) is not None
    }
    return Credential.model_validate(data)


@pytest.fixture(autouse=True)
def skip_unavailable_api_errors():
    """将外部环境不可用导致的 API 异常转为跳过."""
    try:
        yield
    except (CredentialInvalidError, CredentialExpiredError, NetworkError, RatelimitedError) as exc:
        pytest.skip(str(exc))


@pytest_asyncio.fixture
async def client(pytestconfig: pytest.Config) -> AsyncIterator[Client]:
    """创建复用 pytest cache 设备信息的 Client 实例."""
    device_path = pytestconfig.cache.mkdir(TEST_DEVICE_CACHE_DIR) / TEST_DEVICE_FILENAME
    test_client = Client(device_path=str(device_path))
    yield test_client
    await test_client.close()


_credential = _build_credential()


@pytest_asyncio.fixture
async def authenticated_client(pytestconfig: pytest.Config) -> AsyncIterator[Client]:
    """创建复用 pytest cache 设备信息的已认证 Client 实例."""
    if not _credential.musicid:
        raise pytest.skip("未提供有效的测试凭证, 跳过需要登录的测试")
    device_path = pytestconfig.cache.mkdir(TEST_DEVICE_CACHE_DIR) / TEST_DEVICE_FILENAME
    test_client = Client(credential=_credential, device_path=str(device_path))
    yield test_client
    await test_client.close()
