import pytest

from infrastructure.config import Config, ConfigError, load_config


class TestLoadConfig:
    def test_minimum_env_produces_default_base_url(self) -> None:
        cfg = load_config({"JOOTO_API_KEY": "abc"})
        assert cfg == Config(api_key="abc", base_url="https://app.jooto.com")

    def test_base_url_override(self) -> None:
        cfg = load_config(
            {"JOOTO_API_KEY": "abc", "JOOTO_BASE_URL": "https://staging.jooto.com/"}
        )
        assert cfg.base_url == "https://staging.jooto.com"  # trailing slash stripped

    def test_missing_api_key_raises(self) -> None:
        with pytest.raises(ConfigError, match="JOOTO_API_KEY"):
            load_config({})

    def test_blank_api_key_raises(self) -> None:
        with pytest.raises(ConfigError):
            load_config({"JOOTO_API_KEY": "  "})
