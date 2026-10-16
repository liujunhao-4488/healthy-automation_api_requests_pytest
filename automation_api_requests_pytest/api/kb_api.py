# api/kb_api.py
# 【接口层】知识库检索接口 —— RAG 链路里的"检索端"。
#
# ⭐ 为什么单独一个 client、单独一个 base_url
#   它打在**算法服务（Flask，5000 端口）**上，不是 Java 后端（8080）。
#   RAG 的召回测试直连这里：不经 Java、不用登录拿 token、不用同时起两个服务。
#   这样测到的才是"检索本身准不准"，而不是"Java 转发得好不好"——
#   两件事混在一起测，出错时你分不清是谁的锅。
#
# ⚠️ 这个服务**不需要鉴权**（内网服务，Java 侧靠内网调用）。
#   所以这里的方法都不收 headers 参数 —— 不是忘了写。
#
# 路由来源：algorithm/app.py 的 kb_search / kb_stats。

from config.config import KB_BASE_URL

from .base_api_client import BaseApiClient


class KbApi(BaseApiClient):
    # 覆盖底座默认的 Java 后端地址，改打到算法服务
    base_url = KB_BASE_URL

    def search(self, query, top_k=3, source_type=None):
        """POST /api/kb/search —— 按问题检索知识库。

        query       : 用户问题
        top_k       : 返回几条
        source_type : 检索范围。不传 = 服务端默认（authority，只查权威指南）
                      "authority" / "article" / "all"
                      传 None 时**不发这个字段**，让服务端用默认值 ——
                      和"显式传 authority"是两回事：
                      将来服务端默认值一变，这里的用例能测出变化。
        """
        payload = {"query": query, "topK": top_k}
        if source_type is not None:
            payload["sourceType"] = source_type
        return self.post("/api/kb/search", json=payload)

    def stats(self):
        """GET /api/kb/stats —— 看索引构成（多少块、来自哪个源）。"""
        return self.get("/api/kb/stats")

    def reload(self):
        """POST /api/kb/reload —— 重建索引（改了语料后不用重启服务）。

        注意：它只重建**索引**（读 kb_data/authority_chunks.json）。
        改了「权威文件/」里的 PDF 还得先重跑 ingest_authority.py 再调这个。
        """
        return self.post("/api/kb/reload", json={})
