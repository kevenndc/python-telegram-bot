# Chatbot para Telegram

Este bot, no momento, possui 2 funcionalidades.

## Avaliação
É possível selecionar um filme para ser avaliado utilizando o comando:

```bash
/avaliar [termo para pesquisa]
```
onde no lugar de [termo para pesquisa], o usuário deve substituir pelo título de um filme em inglês, SEM OS COLCHETES.

O bot então retornará um lista de título encontrados no IMDB que correspondem ao termo de pesquisa.

Basta selecionar um título da lista e o bot então solicitará uma avaliação de 0,0 a 5,0 para otítulo selecionado.

Após a avaliação ser concluída o bot pode demorar até 20 segundo para mostrar a mensagem de sucesso. Isso acontece pois o mesmo está atualizando as tabelas utilizadas para fazer a recomendação.

## Recomendação
É possível pedir uma recomendação de filme para o bot.

Para pedir uma recomendação utiliza-se o comando:

```bash
/recomendacao
```

Este processo pode demorar até 3 minutos e, quando terminar, o bot notificará o usuário com uma lista de 5 filmes sugeridos.