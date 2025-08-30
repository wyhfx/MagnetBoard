zai1-- 创建数据库扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建数据库（如果不存在）
-- 注意：PostgreSQL容器会自动创建数据库，这里主要是为了确保扩展存在
