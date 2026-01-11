import os
import threading
from pathlib import Path
from typing import Any

from server import default
from server.exceptions import (
    ConfigWriteException,
    ConfigReadException,
    ConfigGenerateException,
)
from utils.encode import json
from utils.server import log


class ConfigManager:
    def __init__(self, config_dir: str = "./data", config_file: str = "config.json"):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录
            config_file: 配置文件名
        """
        self.logger = log.createLogger("Config")
        self._lock = threading.RLock()

        self.config_dir = Path(config_dir)
        self.config_path = self.config_dir / config_file
        self.temp_config_path = self.config_dir / f"{config_file}.tmp"

        self.config: dict = {}

        self._ensure_config_dir()

        self._init_config()
        self.logger.info("已初始化配置管理器")

    def _ensure_config_dir(self) -> None:
        """确保配置目录存在"""
        self.config_dir.mkdir(mode=0o777, parents=True, exist_ok=True)

    def _init_config(self) -> None:
        """初始化配置文件"""
        if not self.config_path.exists():
            self.logger.warning("配置文件不存在，创建默认配置")
            self._generate_default_config()
            return

        try:
            self._load_config()
        except Exception as e:
            self.logger.error(f"配置文件加载失败: {e}，使用默认配置")
            self.config = default.default.copy()

    def _load_config(self) -> None:
        """从文件加载配置"""
        with self._lock:
            content = self.config_path.read_text(encoding="utf-8")

            if not content.strip():
                self.logger.warning("配置文件为空，重新生成默认配置")
                self._generate_default_config()
                return

            self.config = json.loads(content)
            self.logger.info("配置文件加载成功")

    def _generate_default_config(self) -> None:
        """生成默认配置文件"""
        try:
            with self._lock:
                self.config_path.write_text(
                    json.dumps(default.default, indent_2=True),
                    encoding="utf-8"
                )
                self.config = default.default.copy()

                if not os.getenv("build"):
                    self.logger.warning(
                        f"已创建默认配置文件，请修改 {self.config_path.absolute()} 后重新启动"
                    )
                    os._exit(1)

        except Exception as e:
            self.logger.error(f"配置生成失败: {e}")
            raise ConfigGenerateException(e)

    def get(self, key: str, default_value: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键，支持点号分隔的嵌套键（如 'server.port'）
            default_value: 键不存在时的默认值

        Returns:
            配置值或默认值
        """
        try:
            with self._lock:
                keys = key.split(".")
                value = self.config

                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return default_value

                return value

        except Exception as e:
            self.logger.error(f"配置读取失败 [{key}]: {e}")
            raise ConfigReadException(e)

    def set(self, key: str, value: Any) -> None:
        """
        设置配置项并保存到文件

        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        try:
            with self._lock:
                if self.config_path.exists():
                    config = json.loads(self.config_path.read_text(encoding="utf-8"))
                else:
                    config = {}

                keys = key.split(".")
                current = config

                for k in keys[:-1]:
                    if k not in current or not isinstance(current[k], dict):
                        current[k] = {}
                    current = current[k]

                current[keys[-1]] = value

                self._atomic_write(config)

                self.config = config

        except Exception as e:
            self.logger.error(f"配置写入失败 [{key}]: {e}")
            self._cleanup_temp_file()
            raise ConfigWriteException(e)

    def _atomic_write(self, config: dict) -> None:
        """
        原子性写入配置文件

        Args:
            config: 配置字典
        """
        self.temp_config_path.write_text(
            json.dumps(config, indent_2=True),
            encoding="utf-8"
        )

        self.temp_config_path.replace(self.config_path)

    def _cleanup_temp_file(self) -> None:
        """清理临时文件"""
        try:
            if self.temp_config_path.exists():
                self.temp_config_path.unlink()
        except Exception as e:
            self.logger.warning(f"清理临时文件失败: {e}")

    def reload(self) -> None:
        """重新加载配置文件"""
        self.logger.info("重新加载配置文件")
        self._load_config()

    def update(self, updates: dict) -> None:
        """
        批量更新配置项

        Args:
            updates: 要更新的配置字典
        """
        try:
            with self._lock:
                def deep_merge(base: dict, updates: dict) -> dict:
                    for key, value in updates.items():
                        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                            deep_merge(base[key], value)
                        else:
                            base[key] = value
                    return base

                config = self.config.copy() if self.config else {}
                config = deep_merge(config, updates)

                self._atomic_write(config)
                self.config = config

        except Exception as e:
            self.logger.error(f"批量更新配置失败: {e}")
            self._cleanup_temp_file()
            raise ConfigWriteException(e)

    def has(self, key: str) -> bool:
        """
        检查配置项是否存在

        Args:
            key: 配置键

        Returns:
            是否存在
        """
        return self.get(key, default_value=object()) is not object()

    def delete(self, key: str) -> None:
        """
        删除配置项

        Args:
            key: 配置键
        """
        try:
            with self._lock:
                keys = key.split(".")
                config = self.config.copy()
                current = config

                for k in keys[:-1]:
                    if k not in current or not isinstance(current[k], dict):
                        return
                    current = current[k]

                if keys[-1] in current:
                    del current[keys[-1]]
                    self._atomic_write(config)
                    self.config = config

        except Exception as e:
            self.logger.error(f"删除配置失败 [{key}]: {e}")
            self._cleanup_temp_file()
            raise ConfigWriteException(e)


config = ConfigManager()
