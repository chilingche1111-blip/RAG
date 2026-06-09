from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TopicProfile:
    id: str
    label: str
    description: str
    documentation_hint: str
    official_sources: list[dict[str, str]]
    sample_questions: list[str]
    related_questions: list[str]


TOPIC_PROFILES: dict[str, TopicProfile] = {
    "fastapi": TopicProfile(
        id="fastapi",
        label="FastAPI",
        description="FastAPI 路由、依赖注入和异步接口的官方文档知识。",
        documentation_hint="回答 FastAPI 问题时，优先区分路由层、依赖注入层和 async 运行时语义。",
        official_sources=[
            {
                "name": "FastAPI Dependencies",
                "url": "https://fastapi.tiangolo.com/tutorial/dependencies/",
            }
        ],
        sample_questions=[
            "FastAPI 的依赖注入适合解决什么问题？",
            "什么时候该把 FastAPI 接口写成 async？",
            "FastAPI 的子依赖是怎么工作的？",
        ],
        related_questions=[
            "FastAPI 依赖注入和中间件分别适合什么场景？",
            "同步 def 和 async def 路由在 FastAPI 里如何选择？",
            "如果一个依赖被多次声明，FastAPI 会怎样处理？",
        ],
    ),
    "python-asyncio": TopicProfile(
        id="python-asyncio",
        label="Python Asyncio",
        description="Python 官方 asyncio 文档中的协程、任务与并发控制。",
        documentation_hint="解释 asyncio 时，优先讲协程、任务调度和 IO-bound 场景，而不是泛泛地说“异步更快”。",
        official_sources=[
            {
                "name": "Python asyncio",
                "url": "https://docs.python.org/3/library/asyncio.html",
            },
            {
                "name": "Coroutines and Tasks",
                "url": "https://docs.python.org/3/library/asyncio-task.html",
            },
        ],
        sample_questions=[
            "asyncio 适合解决什么类型的问题？",
            "asyncio.create_task 和直接 await 有什么区别？",
            "什么时候应该使用 TaskGroup？",
        ],
        related_questions=[
            "协程、任务和线程各自的职责边界是什么？",
            "如果一个 await 阻塞太久，会对事件循环造成什么影响？",
            "为什么 asyncio 更适合 IO-bound 而不是 CPU-bound 工作负载？",
        ],
    ),
    "redis": TopicProfile(
        id="redis",
        label="Redis",
        description="Redis 官方文档中的持久化、RDB 和 AOF 等核心知识。",
        documentation_hint="Redis 问题建议先明确目标是性能、恢复速度还是数据安全，再解释 RDB 和 AOF 的取舍。",
        official_sources=[
            {
                "name": "Redis Persistence",
                "url": "https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/",
            }
        ],
        sample_questions=[
            "Redis 的 RDB 和 AOF 有什么区别？",
            "为什么 RDB 适合备份？",
            "为什么 AOF 更适合降低数据丢失风险？",
        ],
        related_questions=[
            "什么场景下可以直接关闭 Redis 持久化？",
            "AOF 和 RDB 同时开启时，恢复数据会优先使用哪个？",
            "为什么 fork 对大数据集 Redis 实例会有成本？",
        ],
    ),
    "postgresql": TopicProfile(
        id="postgresql",
        label="PostgreSQL",
        description="PostgreSQL 官方文档中的 B-Tree 和索引基础能力。",
        documentation_hint="解释 PostgreSQL 索引时，最好把“可排序数据类型、树高度和查询模式”连起来讲。",
        official_sources=[
            {
                "name": "PostgreSQL B-Tree Indexes",
                "url": "https://www.postgresql.org/docs/current/btree.html",
            },
            {
                "name": "PostgreSQL Indexes",
                "url": "https://www.postgresql.org/docs/current/indexes.html",
            },
        ],
        sample_questions=[
            "为什么 PostgreSQL 默认使用 B-Tree 索引？",
            "B-Tree 适合哪类查询？",
            "索引为什么会影响写入成本？",
        ],
        related_questions=[
            "什么查询更可能命中 B-Tree？",
            "为什么索引不是越多越好？",
            "叶子页和内部页分别承担什么职责？",
        ],
    ),
    "docker": TopicProfile(
        id="docker",
        label="Docker",
        description="Docker 官方文档中的构建缓存和缓存失效规则。",
        documentation_hint="Docker 构建问题建议按“层、缓存命中、缓存失效、Dockerfile 排序”这条线解释。",
        official_sources=[
            {
                "name": "Docker Build Cache",
                "url": "https://docs.docker.com/build/cache/",
            },
            {
                "name": "Build Cache Invalidation",
                "url": "https://docs.docker.com/build/cache/invalidation/",
            },
        ],
        sample_questions=[
            "Docker 构建缓存是怎么工作的？",
            "为什么 COPY 的变化会导致后续层重建？",
            "怎样写 Dockerfile 更容易命中缓存？",
        ],
        related_questions=[
            "为什么一层失效后后续层也要重建？",
            "依赖安装步骤为什么通常要放在代码复制之前？",
            "CI 环境下为什么外部缓存会更重要？",
        ],
    ),
}


def get_topic_profile(topic: str | None) -> TopicProfile | None:
    if not topic:
        return None
    return TOPIC_PROFILES.get(topic.lower())


def list_topic_profiles() -> list[TopicProfile]:
    return list(TOPIC_PROFILES.values())
