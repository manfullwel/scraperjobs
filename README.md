# JobSearch Pro

Uma API profissional de busca de vagas que integra múltiplas fontes de dados para encontrar as melhores oportunidades.

## Funcionalidades

- Busca de vagas em múltiplas fontes (Adzuna, LinkedIn)
- Interface web moderna e responsiva
- Cache de resultados para melhor performance
- Controle de uso da API
- Suporte a filtros (remoto, localização, etc.)
- Ordenação por data e salário
- Chave pública com limite de 5 buscas para usuários Termux

## Configuração

### Windows/Linux/Mac

1. Clone o repositório
```bash
git clone https://github.com/manfullwel/scraperjobs.git
cd scraperjobs
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure suas próprias chaves da API no arquivo `.env` para ter acesso ilimitado:
```ini
# APIs
ADZUNA_APP_ID="seu_app_id"
ADZUNA_API_KEY="sua_api_key"
```

### Android (Termux)

1. Instale o Termux pela [F-Droid](https://f-droid.org/en/packages/com.termux/) (recomendado) ou Play Store

2. Atualize o Termux e instale as dependências básicas:
```bash
pkg update && pkg upgrade
pkg install python git
```

3. Instale as ferramentas de desenvolvimento:
```bash
pkg install build-essential
pkg install python-dev
```

4. Clone o repositório:
```bash
git clone https://github.com/manfullwel/scraperjobs.git
cd scraperjobs
```

5. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate
```

6. Instale as dependências (pode levar alguns minutos):
```bash
pip install wheel
pip install -r requirements.txt
```

Nota: No Termux, a aplicação usa uma chave pública com limite de 5 buscas por dia por dispositivo. Para acesso ilimitado, configure suas próprias chaves da API no arquivo `.env`.

## Configuração do Ambiente

1. (Opcional) Configure suas próprias chaves da API no arquivo `.env`:
```ini
# APIs (opcional - remova para usar a chave pública)
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

2. Inicie o servidor:
```bash
python main.py
```

3. Acesse a interface web:
- No computador: http://localhost:8000
- No Termux: http://localhost:8000 ou http://127.0.0.1:8000

## Limites de API

### Chave Pública (Termux)
- Limite: 5 buscas por dia por dispositivo
- Não requer configuração
- Ideal para testes e uso pessoal limitado

### Chave Privada
- Limite: 100 buscas por dia (configurável)
- Requer configuração no arquivo `.env`
- Recomendado para uso profissional

Para verificar seu uso atual:
```bash
curl http://localhost:8000/api/usage
```

## Desenvolvimento no Termux

Para desenvolver usando o Termux, você pode:

1. Usar editores de texto no terminal:
```bash
pkg install nano  # ou
pkg install vim
```

2. Usar o VS Code no celular:
- Instale o [Code Server](https://github.com/coder/code-server) no Termux:
```bash
pkg install code-server
code-server
```
- Acesse http://localhost:8080 no navegador do celular

3. Usar um servidor SSH para desenvolver remotamente:
```bash
pkg install openssh
sshd
# Configure uma senha com passwd
```

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

## Solução de Problemas no Termux

1. Se encontrar erros de SSL:
```bash
pkg install openssl
```

2. Se precisar de mais espaço:
```bash
termux-setup-storage
```

3. Para manter o servidor rodando após fechar o Termux:
```bash
pkg install tmux
tmux
python main.py
# Ctrl+B, D para desanexar
```

4. Para ver logs em tempo real:
```bash
tail -f nohup.out
```

5. Se exceder o limite de buscas:
- Aguarde 24 horas para o limite ser resetado, ou
- Configure suas próprias chaves da API no arquivo `.env`

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
