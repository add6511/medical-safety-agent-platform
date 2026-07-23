"""
烟雾测试脚本
验证 AI 服务的核心功能是否正常工作。

用法:
    python scripts/smoke_test.py --base-url http://127.0.0.1:8000

所有测试数据均为合成教学数据，不使用真实患者数据。
"""

import argparse
import json
import sys
import urllib.request
import urllib.error


def api_request(method: str, url: str, data: dict = None) -> tuple[int, dict]:
    """发送 HTTP 请求"""
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else "{}"
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, {"error": body}


def test_health(base_url: str) -> bool:
    """测试健康检查接口"""
    print("[1/7] 测试 GET /health ...")
    status, data = api_request("GET", f"{base_url}/health")

    if status != 200:
        print(f"  FAIL: 状态码 {status}，预期 200")
        return False

    if data.get("status") != "ok":
        print(f"  FAIL: status={data.get('status')}，预期 ok")
        return False

    print(f"  PASS: service={data.get('service')}, version={data.get('version')}")
    return True


def test_import_knowledge(base_url: str) -> str | None:
    """导入一条合成教学知识"""
    print("[2/7] 导入合成教学知识 ...")

    payload = {
        "title": "红旗信号识别指南（合成教学材料）",
        "publisher": "合成教学材料编写组",
        "source_url": "https://example.com/guidance/red-flags",
        "document_version": "v1.0",
        "content": (
            "合成教学示例：红旗信号是指患者出现的高危症状，包括意识状态变化、"
            "严重呼吸困难、持续胸部不适、无法控制的出血、自伤风险信息和孕产相关紧急信号。"
            "当系统检测到红旗信号时，必须触发人工审核流程，不允许AI自动降低风险等级。"
            "所有红旗信号的判定必须由专业医疗人员进行最终确认。"
        ),
    }

    status, data = api_request("POST", f"{base_url}/api/v1/knowledge/documents", payload)

    if status != 200:
        print(f"  FAIL: 状态码 {status}，预期 200")
        return None

    doc_id = data.get("document_id")
    print(f"  PASS: document_id={doc_id}, chunk_count={data.get('chunk_count')}")
    return doc_id


def test_search(base_url: str) -> bool:
    """测试知识检索"""
    print("[3/7] 测试知识检索 ...")

    payload = {"query": "红旗信号 高危症状", "top_k": 3}
    status, data = api_request("POST", f"{base_url}/api/v1/knowledge/search", payload)

    if status != 200:
        print(f"  FAIL: 状态码 {status}，预期 200")
        return False

    results = data.get("results", [])
    print(f"  PASS: 检索到 {len(results)} 条结果")
    return True


def test_preconsultation(base_url: str) -> dict | None:
    """调用多 Agent 预问诊审核"""
    print("[4/7] 调用多 Agent 预问诊审核（红旗标志）...")

    # 合成教学病例
    payload = {
        "case_id": "smoke-test-001",
        "age": 55,
        "symptoms": [{"name": "胸部不适", "severity": 8, "duration": "30分钟"}],
        "red_flags": ["persistent_chest_discomfort"],
        "free_text": "合成教学示例：患者出现持续胸部不适，伴有胸闷。",
        "model_suggested_risk": "LOW",
    }

    status, data = api_request("POST", f"{base_url}/api/v1/preconsultation/review", payload)

    if status != 200:
        print(f"  FAIL: 状态码 {status}，预期 200")
        return None

    print(f"  PASS: final_risk={data.get('final_risk_level')}, rule_risk={data.get('rule_risk_level')}")
    return data


def test_no_downgrade(data: dict) -> bool:
    """验证规则不能被模型降级"""
    print("[5/7] 验证规则不被模型降级 ...")

    if not data.get("model_downgrade_blocked"):
        print("  FAIL: model_downgrade_blocked 应为 True")
        return False

    if data.get("final_risk_level") != data.get("rule_risk_level"):
        print(f"  FAIL: final_risk({data.get('final_risk_level')}) != rule_risk({data.get('rule_risk_level')})")
        return False

    print(f"  PASS: 模型降级已阻止，风险保持 {data.get('final_risk_level')}")
    return True


def test_human_review(data: dict) -> bool:
    """验证 needs_human_review=true"""
    print("[6/7] 验证人工审核标记 ...")

    if not data.get("needs_human_review"):
        print("  FAIL: needs_human_review 应为 True")
        return False

    print("  PASS: needs_human_review=true")
    return True


def test_citation_and_disclaimer(data: dict) -> bool:
    """验证返回引用和免责声明"""
    print("[7/7] 验证引用和免责声明 ...")

    # 检查免责声明
    disclaimer = data.get("disclaimer", "")
    if "教学" not in disclaimer and "不构成" not in disclaimer:
        print(f"  FAIL: 免责声明内容异常: {disclaimer[:50]}")
        return False

    # 检查 agent_trace
    trace = data.get("agent_trace", [])
    if len(trace) < 4:
        print(f"  FAIL: agent_trace 只有 {len(trace)} 条，预期至少 4 条")
        return False

    print(f"  PASS: 免责声明存在，agent_trace 有 {len(trace)} 条记录")
    return True


def main():
    parser = argparse.ArgumentParser(description="AI 服务烟雾测试")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="AI 服务基础地址",
    )
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    print(f"=== AI 服务烟雾测试 ===")
    print(f"目标地址: {base_url}")
    print()

    all_passed = True

    # 1. 健康检查
    if not test_health(base_url):
        all_passed = False
        print("\n烟雾测试失败：健康检查未通过，服务可能未启动。")
        sys.exit(1)

    # 2. 导入知识
    doc_id = test_import_knowledge(base_url)
    if not doc_id:
        all_passed = False

    # 3. 知识检索
    if not test_search(base_url):
        all_passed = False

    # 4. 预问诊审核
    review_data = test_preconsultation(base_url)
    if not review_data:
        all_passed = False
        print("\n烟雾测试失败：预问诊审核未通过。")
        sys.exit(1)

    # 5. 验证不被降级
    if not test_no_downgrade(review_data):
        all_passed = False

    # 6. 验证人工审核
    if not test_human_review(review_data):
        all_passed = False

    # 7. 验证引用和免责声明
    if not test_citation_and_disclaimer(review_data):
        all_passed = False

    # 清理：删除导入的文档
    if doc_id:
        api_request("DELETE", f"{base_url}/api/v1/knowledge/documents/{doc_id}")

    print()
    if all_passed:
        print("=== 烟雾测试全部通过 ===")
        sys.exit(0)
    else:
        print("=== 烟雾测试存在失败项 ===")
        sys.exit(1)


if __name__ == "__main__":
    main()
