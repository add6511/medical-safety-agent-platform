"""
OpenAPI 规范导出脚本
从 FastAPI app 真实生成 OpenAPI JSON，不启动网络服务。

用法:
    python scripts/export_openapi.py

输出:
    docs/openapi.json
"""

import json
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.main import app


def main():
    """导出 OpenAPI JSON"""
    # 获取 OpenAPI schema
    openapi_schema = app.openapi()

    # 确保输出目录存在
    output_dir = Path(_project_root) / "docs"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "openapi.json"

    # 写入 JSON（格式化缩进，UTF-8）
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, ensure_ascii=False, indent=2)

    print(f"OpenAPI 规范已导出: {output_path}")
    print(f"接口数量: {len(openapi_schema.get('paths', {}))}")

    # 列出所有接口
    for path, methods in openapi_schema.get("paths", {}).items():
        for method in methods:
            if method in ("get", "post", "put", "delete", "patch"):
                print(f"  {method.upper()} {path}")


if __name__ == "__main__":
    main()
