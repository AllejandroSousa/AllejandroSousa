# 0001 — Animação do README: SVG com sprite sheet PNG embutido

Data: 2026-11-15

## Contexto

O README do perfil mostra uma animação em pixel-art: o Homem-Aranha agachado num telhado
salta e balança por uma avenida no estilo Times Square, com telões das stacks (Ruby, Python,
JavaScript, C++, Hugging Face, AppSec). A câmera é em terceira pessoa, com perspectiva real.

O GitHub remove JavaScript do README, mas mantém animação CSS dentro de imagens SVG.

## Decisão

Um renderizador 3D → pixel-art em Python puro (`animation/`) gera cada quadro (240×100).
Os quadros distintos vão para um único PNG com paleta de 8 bits, embutido em base64 num SVG.
Uma animação CSS `steps()` troca o quadro visível. A chuva e o relâmpago são vetoriais, por cima.

Regenerar: `python3 -m animation spiderman.svg` (~25 s). Testes: `python3 -m unittest discover -s tests -t .`

## Alternativas descartadas

- **SVG vetorial puro (versão 1, vista lateral):** leve (113 KB), mas não comporta perspectiva:
  paredes laterais e texturas mudam de forma a cada quadro.
- **GIF/WebP renderizado:** maior, borrado ao escalar e sem `prefers-reduced-motion`.
- **PNG RGB no sprite sheet:** 1,2 MB; com paleta caiu para ~600 KB, alterando cerca de 100 de
  2,6 milhões de pixels.

## Consequências

- O SVG pesa ~600 KB. Mais quadros ou mais resolução aumentam o tamanho quase linearmente.
- O loop é contínuo porque a cidade se repete a cada `PERIOD` e o último quadro reaproveita
  as coordenadas do primeiro. Um teste garante isso pixel a pixel.
- `image-rendering: pixelated` mantém a nitidez; navegadores sem suporte mostram o desenho suavizado.
