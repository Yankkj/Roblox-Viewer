#  Gon Roblox Viewer

**Viewer avançado de contas Roblox com notificações em tempo real via Discord**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Custom-red.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-3.1.0-green.svg)](https://github.com/Yankkj)

[Recursos](#-recursos) • [Instalação](#-instalação) • [Configuração](#️-configuração)

</div>

---

## Sobre

**Gon Roblox Viewer** é um sistema de monitoramento em tempo real para contas do Roblox que detecta e notifica via Discord webhooks sobre diversas mudanças na conta, incluindo:

- Amigos (adições/remoções)
- Seguidores e seguindo
- Grupos (entradas/saídas/mudanças de cargo)
- Status de presença
- Alterações de avatar/skin
- Novos badges conquistados
- Estatísticas completas da conta

## Recursos

### Notificações Inteligentes
- **Batching automático**: Agrupa múltiplas mudanças em embeds organizados
- **Deduplicação**: Evita notificações duplicadas no mesmo ciclo
- **Quiet Hours**: Silencia notificações em horários específicos
- **Embeds ricas**: Notificações visualmente atraentes com avatares e links

### Performance Otimizada
- **Cache inteligente**: Reduz chamadas desnecessárias à API do Roblox
- **Rate limiting**: Respeita limites de requisição automaticamente
- **Async/await**: Operações concorrentes para máxima velocidade
- **Retry automático**: Recuperação de falhas de rede com backoff exponencial

### Monitoramento Preciso
- **Detecção de avatares**: Usa assinatura SHA256 para detectar mudanças reais
- **Window com rotação**: Monitora followers/followings de forma eficiente
- **Full refresh periódico**: Garante sincronização completa dos dados
- **Backup de estado**: Preserva histórico entre execuções

## Instalação

### Requisitos
- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)

### Instalação Rápida

```bash
# Clone o repositório
git clone https://github.com/Yankkj/gon-roblox-viewer.git
cd gon-roblox-viewer

# Instale as dependências
pip install aiohttp>=3.9.0

# Configure o arquivo de configuração
cp config.example.json config.json
# Edite config.json com seus dados
```

## Configuração

### 1. Obter Webhook do Discord

1. Acesse as configurações do seu servidor Discord
2. Vá em **Integrações** → **Webhooks**
3. Clique em **Novo Webhook**
4. Copie a URL do webhook


### Parâmetros Principais

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `webhook_url` | URL do webhook do Discord | **Obrigatório** |
| `user_ids` | Lista de IDs Roblox para monitorar | `[123456789]` |
| `check_interval` | Intervalo entre verificações (segundos) | `30` |
| `window_limit` | Quantos followers/followings monitorar | `200` |
| `full_refresh_every` | Ciclos até refresh completo | `10` |
| `batch_max_items` | Máximo de itens por embed em lote | `15` |

## Como Funciona

### Ciclo de Monitoramento

1. **Coleta de dados**: API Roblox é consultada para obter informações atuais
2. **Comparação**: Estado atual é comparado com estado anterior (diff)
3. **Detecção de mudanças**: Algoritmo identifica o que mudou
4. **Notificação**: Embeds são criados e enviados via webhook
5. **Persistência**: Estado atualizado é salvo para próximo ciclo

### Estratégia de Otimização

- **Count-first**: Verifica contadores antes de listar (economia de requests)
- **Window rotation**: Alterna entre Asc/Desc para capturar mudanças em ambas extremidades
- **Cache TTL**: Perfis em cache por 5 minutos
- **Batch processing**: Agrupa operações para reduzir webhooks



## Troubleshooting

### Erro: "Bloqueado: owner inválido"
- Verifique se os campos `owner` em `config.json` estão corretos
- Não modifique os valores padrão de `owner`

### Erro: "Bloqueado: tokens ausentes/alterados"
- Os arquivos do módulo `viewer/` foram modificados
- Restaure os arquivos originais do repositório

### Webhook não recebe notificações
- Confirme que a URL do webhook está correta
- Verifique se `silent_mode` está `false`
- Confira se não está em horário silencioso (`quiet_hours`)

### Rate Limit (429 errors)
- Aumente o `check_interval` (recomendado: >= 30s)
- Reduza `window_limit` para diminuir requests
- Monitore métricas HTTP no terminal

## Autor

**Yankkj**
- GitHub: [@Yankkj](https://github.com/Yankkj)
- Discord: revivem

---

<div align="center">

**Gon Roblox Viewer** 

Desenvolvido por [@Gon](https://github.com/Yankkj)

</div>