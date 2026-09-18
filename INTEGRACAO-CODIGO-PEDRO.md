# Integração do código do Pedro

O código recebido foi preservado como base do projeto: Django, app
`doacoes`, banco SQLite, formulários, reservas, coletas, painel e endpoint
JSON continuam integrados.

## Autenticação atual

- O acesso usa somente a autenticação nativa do Django por e-mail/usuário e
  senha.
- O cadastro cria a conta e o perfil de doador ou recebedor no banco.
- **Não há Firebase, OAuth, botão Google** nem arquivos de configuração do Google.
- Páginas internas continuam protegidas por sessão e `login_required`.

## Organização visual

- `static/css/ifeed.css`: sistema visual compartilhado e área interna.
- `static/css/django-extra.css`: formulários e componentes ligados ao Django.
- `static/css/concept-art.css`: fidelidade das páginas públicas às concept
  arts.
- `static/assets/icons/concept/`: ícones fornecidos, separados um a um em
  PNG transparente.
- `static/js/site.js`: menu, FAQ, ViaCEP e gráficos interativos.
- `static/js/mapa-doacoes.js`: mapa de doações disponíveis (geolocalização).

O projeto não depende de Node, Vite, React ou serviços externos de
autenticação para iniciar no VS Code.
