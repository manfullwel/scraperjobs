# JobSearch Pro

Uma API profissional de busca de vagas que integra múltiplas fontes de dados para encontrar as melhores oportunidades.

## Funcionalidades

- Busca de vagas em múltiplas fontes (Adzuna, LinkedIn)
- Interface web moderna e responsiva
- Cache de resultados para melhor performance
- Controle de uso da API
- Suporte a filtros (remoto, localização, etc.)
- Ordenação por data e salário

## Configuração

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente no arquivo `.env`:
```ini
# APIs
ADZUNA_APP_ID="seu_app_id"
ADZUNA_API_KEY="sua_api_key"

# Cache
CACHE_ENABLED=True
CACHE_TTL=3600
CACHE_MAX_SIZE=1000

# API Usage
API_DAILY_LIMIT=100
API_USAGE_FILE="api_usage.json"
```

4. Inicie o servidor:
```bash
python main.py
```

5. Acesse a interface web em: http://localhost:8000

## Estrutura do Projeto

```
.
├── main.py              # Ponto de entrada da aplicação
├── requirements.txt     # Dependências do projeto
├── .env                # Configurações do ambiente
└── src/
    ├── api/            # Endpoints da API
    ├── models/         # Modelos de dados
    ├── scrapers/       # Scrapers para diferentes fontes
    ├── services/       # Lógica de negócio
    ├── static/         # Arquivos estáticos (CSS, JS)
    └── templates/      # Templates HTML
```

## API Endpoints

### POST /api/jobs/search
Busca vagas com os parâmetros especificados.

**Parâmetros:**
- `keywords`: Palavras-chave para busca
- `location`: Localização
- `remote_only`: Apenas vagas remotas (opcional)
- `sources`: Lista de fontes para busca (opcional)

### GET /api/usage
Obtém estatísticas de uso da API.

## Próximos Passos

- [ ] Adicionar mais fontes de dados
- [ ] Implementar autenticação de usuários
- [ ] Adicionar testes automatizados
- [ ] Melhorar o tratamento de erros
- [ ] Implementar sistema de notificações

## Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes.
