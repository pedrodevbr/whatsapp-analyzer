# Whatsapp Analyzer

Ferramenta em Python para analisar conversas exportadas do WhatsApp. O usuario informa um arquivo ZIP da exportacao oficial e recebe estatisticas, insights e (opcionalmente) recomendacoes geradas por LLM.

## Requisitos

- Python 3.11 ou superior
- (Opcional) conta na OpenAI com a variavel de ambiente `OPENAI_API_KEY` definida
- Dependencias listadas em `requirements.txt`

## Como usar

1. Instale as dependencias (somente necessario se for usar LLM):
    pip install -r requirements.txt
2. Rode o analisador apontando para o ZIP exportado:
    python -m whatsapp_analyzer.cli "Conversa do WhatsApp com Louisy.zip"
3. Para incluir as sugestoes personalizadas vindas de LLM:
    set OPENAI_API_KEY=seu_token_aqui
    python -m whatsapp_analyzer.cli "Conversa.zip" --llm
    Use `--llm-dry-run` para testar o fluxo sem acionar a API.

## Principais recursos

- Pontuacao automatica do relacionamento (0-100) considerando equilibrio, engajamento, emojis, tempo de resposta e sentimento
- Tempo medio de resposta geral e por participante
- Analise simples de sentimento com base em palavras positivas/negativas
- Contagem de mensagens totais, por participante e por horario
- Distribuicao por dia da semana e por data completa
- Palavras mais usadas por participante (ignorando termos genericos)
- Deteccao simples de emojis mais frequentes
- Geracao de resumo textual com insights
- Sugestoes de negocio inspiradas em product management
- Integracao opcional com LLM da OpenAI para produzir ate cinco recomendacoes praticas

## Notas de implementacao

- O parser suporta o formato `DD/MM/AAAA HH:MM - Nome: mensagem`, com multiplas linhas por mensagem.
- Mensagens do sistema sao identificadas automaticamente e excluidas de algumas metricas.
- Placeholders como `<Arquivo de midia oculta>` sao ignorados das contagens de palavras.
- O CLI tenta configurar `stdout` para UTF-8 em Windows para exibir emojis corretamente.

Novas metricas (ex: sentimento, tempo de resposta) podem ser adicionadas extendendo `analysis.py` e `insights.py`.
