# Guia de alterações — versão unificada (Lucio + Altere)

> Esta é a versão **convergida**. Contém o visual/concept arts do Lucio e as funcionalidades de mapa/geolocalização do Altere.
> Login com Google/Firebase foi removido.

# Guia rápido de alterações do iFeed

## Onde mudar cada parte

| Parte | Arquivo ou pasta |
| --- | --- |
| Textos das páginas públicas | `templates/public/` |
| Telas de login e cadastro | `templates/auth/` |
| Painel e demais telas internas | `templates/internal/` |
| Cabeçalho e rodapé públicos | `templates/base_public.html` |
| Menu lateral interno | `templates/base_internal.html` |
| Cores e layouts gerais | `static/css/ifeed.css` |
| Fidelidade das páginas públicas às concept arts | `static/css/concept-art.css` |
| Ajustes Django e formulários | `static/css/django-extra.css` |
| Interações, gráfico e ViaCEP | `static/js/site.js` |
| Ícones PNG gerais | `static/assets/icons/` e `static/js/icons.js` |
| Ícones separados das concept arts | `static/assets/icons/concept/` |
| Login e cadastro por e-mail | `templates/auth/`, `doacoes/forms.py` e `doacoes/views.py` |
| Banco e campos de doação | `doacoes/models.py` |
| Validações de formulários | `doacoes/forms.py` |
| Regras e páginas | `doacoes/views.py` |
| Endereços do site | `doacoes/urls.py` |
| Dados de demonstração | `doacoes/management/commands/seed_ifeed.py` |

## Cores principais

No início de `static/css/ifeed.css`, procure `:root`. As variáveis mais importantes são:

- `--green`: verde principal;
- `--green-dark`: verde escuro;
- `--yellow`: amarelo de destaque;
- `--navy`: azul da identidade;
- `--ink`: textos escuros;
- `--line`: bordas suaves.

## Alterar logo e fotografias

Substitua os arquivos dentro de `static/assets/img/` mantendo exatamente o mesmo nome. Assim, não será necessário mudar os templates.

A logo oficial é `static/assets/img/logo-ifeed.png`. Ela já possui fundo transparente e espaço interno reduzido, por isso se adapta ao cabeçalho público, ao menu lateral e às telas de autenticação.

O selo de prata é `static/assets/img/badge-silver.png`. O arquivo possui margem transparente de segurança e o CSS usa `object-fit: contain`, impedindo cortes em qualquer página.

## Alterar o gráfico de Impacto

- Os valores e períodos são preparados em `doacoes/views.py`, nas funções `_grafico_impacto` e `_grafico_impacto_publico`.
- A renderização, troca de período, animação e tooltip estão em `static/js/site.js`.
- O visual dos eixos, linha, área e botões está no bloco final de `static/css/ifeed.css`.

## Layout expandido e concept arts

O arquivo `static/css/concept-art.css` controla a adaptação das referências para páginas web completas. Nele estão:

- seções públicas em largura total;
- espaçamento lateral responsivo;
- barra lateral interna em altura total;
- área principal sem moldura externa;
- ajustes de login, cadastro, tablet e celular.

Os ícones fornecidos nas pranchas foram separados individualmente, sem
redesenho, e estão organizados em `static/assets/icons/concept/`. Para trocar
um deles, mantenha o mesmo nome de arquivo e use PNG com fundo transparente.

## Adicionar um novo campo

1. Adicione o campo em `doacoes/models.py`.
2. Inclua ou ajuste o campo em `doacoes/forms.py`.
3. Exiba o campo no template desejado.
4. Execute `python manage.py makemigrations` e `python manage.py migrate`.

## Regra importante

As validações essenciais ficam no Django. O JavaScript melhora a experiência, mas o sistema não depende dele para proteger ou salvar informações.
