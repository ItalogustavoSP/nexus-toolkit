Nexus Toolkit

Nexus Toolkit é um conjunto de ferramentas para diagnóstico, monitoramento e manutenção segura de computadores Windows.

Objetivos
Apresentar informações úteis sobre o sistema.
Monitorar recursos e processos do computador.
Analisar o uso do armazenamento.
Identificar arquivos duplicados.
Exibir indicadores do sistema e gráficos de utilização em tempo real.
Oferecer ferramentas de diagnóstico com confirmação explícita.
Gerar relatórios de diagnóstico.
Manter uma arquitetura modular e preparada para futuras extensões.
Princípios do projeto
Prioridade para execução local e funcionamento offline.
Sem anúncios, login, contas ou telemetria por padrão.
Preferências do aplicativo armazenadas localmente.
Ações destrutivas protegidas por confirmação.
Separação entre interface, regras de negócio e acesso ao sistema.
Testes automatizados e documentação.
Código organizado para facilitar contribuições.
Tecnologias
Python
PySide6 / Qt
psutil para métricas locais do sistema
Gráficos nativos Qt, sem dependência de serviços externos
SQLite, quando necessário para persistência local
pytest
Ruff
mypy
Status

Em desenvolvimento inicial. Os recursos serão implementados e testados gradualmente.

Desenvolvimento

O projeto utiliza um ambiente virtual Python para isolar suas dependências.

Ative o ambiente virtual antes de executar os comandos de desenvolvimento.

Testes
python -m pytest
Análise de código
python -m ruff check .
Formatação
python -m ruff format .
Segurança

O Nexus Toolkit deve priorizar ações transparentes, permissões mínimas e confirmação antes de operações que possam alterar ou excluir dados.