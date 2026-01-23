# MAESTRO Backend Structure

## Directory Organization

### `/agents`
- **`/base`**: Base agent classes that all agents inherit from
- **`/specialized`**: Specialized agent implementations
  - `internal_agent.py`: RAG-based internal knowledge retrieval
  - `web_agent.py`: Real-time web intelligence
- `master_agent_enhanced.py`: LangGraph-based orchestration

### `/api`
- **`/endpoints`**: API route handlers
- **`/middleware`**: Request/response middleware
- **`/schemas`**: Pydantic models for request/response validation

### `/config`
- **`/agents`**: Agent-specific configurations (YAML)
- **`/databases`**: Database connection configurations
- **`/llm`**: LLM provider settings

### `/langchain_config`
- **`/chains`**: LangChain chain definitions
- **`/graphs`**: LangGraph workflow definitions
- **`/prompts`**: Prompt templates
- **`/tools`**: Custom tool implementations

### `/vector_store`
- **`/embeddings`**: Embedding models and cache
- **`/indices`**: Vector database indices
- **`/documents`**: Source documents for RAG

### `/services`
- **`/orchestration`**: Agent coordination logic
- **`/query_processing`**: Query understanding and decomposition
- **`/report_generation`**: Report creation services

### `/tests`
- **`/unit`**: Unit tests for individual components
- **`/integration`**: Integration tests for workflows
- **`/fixtures`**: Test data and mocks

## Key Files

- `master_agent_enhanced.py`: LangGraph-based Master Agent
- `agents/specialized/internal_agent.py`: Internal knowledge RAG agent
- `agents/specialized/web_agent.py`: Web intelligence agent
- `config/agents/agent_config.yaml`: Agent configuration
- `utils/cache/cache_manager.py`: Redis-based caching
- `utils/logging/logger.py`: Structured logging

## Next Steps

1. Implement LangGraph workflows in `/langchain_config/graphs`
2. Set up vector store for internal documents
3. Configure agent prompts in `/langchain_config/prompts`
4. Implement data source connectors
5. Create comprehensive tests
6. Set up monitoring and logging
