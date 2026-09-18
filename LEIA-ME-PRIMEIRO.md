# iFeed — versão unificada (Lucio Icons + Altere)

Esta versão **converge** as alterações feitas em paralelo:

- **Projeto-IFEED-Lucio-Icons**: visual completo com concept arts, 40+ ícones PNG separados, `concept-art.css`, identidade visual refinada e autenticação Django por e-mail/senha.
- **Projeto-IFEED-altere**: geolocalização (latitude/longitude), mapa de doações, status "A caminho", urgência e endpoint JSON do mapa.
- **Arthur (Pasta Perfil)**: abas funcionais na tela de Perfil.
- **Concept Art V2**: ícones e imagens públicas ajustados (journey, impacto, tamanhos).

**Login com Google / Firebase foi removido** — o acesso é apenas por e-mail e senha nativos do Django.

## O que foi unificado

| Recurso | Origem |
| --- | --- |
| Concept arts, ícones concept/, concept-art.css | Lucio |
| Visual público e interno refinado | Lucio |
| Campos latitude/longitude no modelo Doacao | Altere |
| Migration 0002 | Altere |
| Endpoint `/doacoes-disponiveis/dados/` + mapa | Altere |
| Botão "Usar minha localização" no formulário de doação | Altere + JS |
| Status "a_caminho" e propriedade `esta_urgente` | Altere |
| Autenticação e-mail/senha Django | Ambos (sem Google) |
| Abas da tela de Perfil | Arthur |

## Conta demonstrativa

- E-mail: `demo@ifeed.com`
- Senha: `Ifeed@2026`
- Recebedora: `ong@ifeed.com` (mesma senha)

## Como executar (Windows)

1. Extraia o ZIP.
2. Abra a pasta no VS Code.
3. Dê dois cliques em `INICIAR_IFEED.bat`.
4. Acesse `http://127.0.0.1:8000/`.

Ou manualmente:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_ifeed
python manage.py runserver
```

## Estrutura

- `doacoes/` — models (com lat/long), views (mapa), forms, migrations
- `static/css/concept-art.css` + `ifeed.css` (com estilos de mapa)
- `static/assets/icons/concept/` — ícones das pranchas
- `static/js/mapa-doacoes.js`, `site.js`

Bom trabalho ao grupo!
