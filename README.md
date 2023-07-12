# EstaciUFBA
Sistema de gerenciamento de estacionamento da UFBA. Projeto da disciplina de Laboratório de Banco de Dados.
Visando testar as funcionalidades do bacon de dados Couchbase.

## Pré-requisitos
Para rodar o projeto é necessário ter o docker e o docker-compose instalados.

## Instalação
Para instalar o projeto basta clonar o repositório e rodar o comando:
```
docker-compose build
```
## Execução
Para executar o projeto basta rodar o comando:
```
docker-compose up estaciufba
```
## Funcionamento
### entrypoint.sh
O arquivo `entrypoint.sh` é responsável por criar e configurar os clusters do Couchbase.

- Ele é executado toda vez que o container é iniciado e cria os buckets `estaciufba` com as coleções `estacionamentos` `vagas` e `vagas_livres`.
- Ele também cria um backup do bucket `estaciufba`.
- 
### src/main.py
O arquivo `src/main.py` é responsável por testar as funcionalidades do banco de dados. Ele é executado toda vez que o container é iniciado.
Funcionalidades testadas:
- Inserção de dados.
- Índices.
- Views.
- Stored Procedures.
- Gestão de usuários.
- Transações.
- Controle de concorrência.

## Estrutura banco de dados
- Dois clusters diferentes para testar o XDCR.
- Cada cluster tem dois nós para testar a replicação.
Verificar o arquivos `entrypoint.sh` e `docker-compose.yml` para mais detalhes.




