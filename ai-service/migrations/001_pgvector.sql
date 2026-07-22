-- ============================================================
-- pgvector 迁移脚本：001_pgvector.sql
-- 用于初始化向量数据库，支持知识库的向量存储和相似度检索
-- 适用数据库：PostgreSQL 14+ 配合 pgvector 扩展
-- ============================================================

-- 启用 pgvector 扩展（如果尚未安装）
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- 文档元信息表
-- 存储导入文档的基本信息，不存储文档正文
-- ============================================================
CREATE TABLE IF NOT EXISTS knowledge_documents (
    -- 文档唯一标识（UUID）
    document_id     VARCHAR(36)     PRIMARY KEY,
    -- 文档标题
    title           VARCHAR(500)    NOT NULL,
    -- 发布机构
    publisher       VARCHAR(200)    NOT NULL,
    -- 来源链接
    source_url      VARCHAR(2000)   NOT NULL,
    -- 文档版本
    document_version VARCHAR(50)    NOT NULL,
    -- 发布时间（可选）
    published_at    TIMESTAMPTZ,
    -- 文档内容 SHA-256 校验值，用于去重
    checksum        VARCHAR(64)     NOT NULL,
    -- 切分后的知识块数量
    chunk_count     INTEGER         NOT NULL DEFAULT 0,
    -- 导入时间
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    -- checksum 唯一约束：保证相同内容不重复导入
    CONSTRAINT uq_knowledge_documents_checksum UNIQUE (checksum)
);

-- 文档表索引
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_created_at
    ON knowledge_documents (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_publisher
    ON knowledge_documents (publisher);

-- ============================================================
-- 知识块表
-- 存储文档切分后的知识块及其向量表示
-- ============================================================
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    -- 知识块唯一标识（UUID）
    chunk_id        VARCHAR(36)     PRIMARY KEY,
    -- 所属文档标识（外键）
    document_id     VARCHAR(36)     NOT NULL
        REFERENCES knowledge_documents (document_id) ON DELETE CASCADE,
    -- 块在文档中的序号（从 0 开始）
    chunk_index     INTEGER         NOT NULL,
    -- 知识块内容
    content         TEXT            NOT NULL,
    -- 文档标题（冗余存储，便于检索返回）
    title           VARCHAR(500)    NOT NULL,
    -- 发布机构
    publisher       VARCHAR(200)    NOT NULL,
    -- 来源链接
    source_url      VARCHAR(2000)   NOT NULL,
    -- 文档版本
    document_version VARCHAR(50)    NOT NULL,
    -- 发布时间
    published_at    TIMESTAMPTZ,
    -- 文档校验值（冗余存储，便于查询）
    checksum        VARCHAR(64)     NOT NULL,
    -- 向量嵌入（默认 384 维，余弦相似度）
    embedding       vector(384)     NOT NULL,
    -- 同一文档内块序号唯一
    CONSTRAINT uq_knowledge_chunks_doc_index UNIQUE (document_id, chunk_index)
);

-- 知识块表索引
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_document_id
    ON knowledge_chunks (document_id);

-- 余弦相似度索引（IVFFlat 或 HNSW，取决于数据量）
-- 数据量较小时使用 HNSW，效果更好
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding
    ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- ============================================================
-- 注释说明
-- ============================================================
COMMENT ON TABLE knowledge_documents IS '知识库文档元信息表';
COMMENT ON TABLE knowledge_chunks IS '知识库知识块表，包含向量嵌入';
COMMENT ON COLUMN knowledge_chunks.embedding IS '知识块的向量表示，用于余弦相似度检索';
COMMENT ON COLUMN knowledge_documents.checksum IS '文档内容 SHA-256 校验值，保证幂等导入';
