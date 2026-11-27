-- Ajustes para el PDF del informe.
-- 1. Cada sección principal empieza en una página nueva.
-- 2. Las fórmulas de los títulos se escriben como texto en los marcadores del PDF.
-- 3. Las figuras ocupan el ancho de la página sin pasar de un 60 % de su alto.
-- 4. Un bloque de código de hasta 25 líneas no se corta entre dos páginas.
-- 5. Las tablas anchas se achican y reparten el ancho según su contenido, de modo
--    que los conjuntos y fórmulas (que no se pueden cortar) quepan en su columna.
--    Una lista de arcos escrita en una sola fórmula, como $(C,G), (D,H)$, se separa
--    en una fórmula por arco para que pueda continuar en la línea siguiente.

local reemplazos = {
  ["\\to"] = "→",
  ["\\setminus"] = "∖",
  ["\\lbrace"] = "{",
  ["\\rbrace"] = "}",
  ["\\lvert"] = "|",
  ["\\rvert"] = "|",
}

local function texto_plano(formula)
  local texto = formula
  for comando, simbolo in pairs(reemplazos) do
    texto = texto:gsub(comando, simbolo)
  end
  texto = texto:gsub("\\[a-zA-Z]+", ""):gsub("%s+", " ")
  return texto
end

function Header(h)
  h.content = h.content:walk({
    -- El texto plano va como Str para que pandoc también lo use en el marcador.
    Math = function(m)
      return {
        pandoc.RawInline("latex", "\\texorpdfstring{$" .. m.text .. "$}{"),
        pandoc.Str(texto_plano(m.text)),
        pandoc.RawInline("latex", "}"),
      }
    end,
  })
  if h.level == 1 then
    return { pandoc.RawBlock("latex", "\\clearpage"), h }
  end
  return h
end

function CodeBlock(bloque)
  local _, saltos = bloque.text:gsub("\n", "")
  local lineas = saltos + 1
  if lineas > 25 then return bloque end
  return {
    pandoc.RawBlock("latex", string.format("\\necesitoespacio{%.1f\\baselineskip}", lineas * 1.1 + 1)),
    bloque,
  }
end

function Image(img)
  if not img.attributes.width and not img.attributes.height then
    return pandoc.RawInline(
      "latex",
      "\\includegraphics[width=\\linewidth,height=0.6\\textheight,keepaspectratio]{"
        .. img.src .. "}"
    )
  end
  return img
end

-- Ancho útil de la línea (16 cm, en puntos) y ancho medio de un carácter según el
-- tamaño de letra. Cada columna pierde además 12 pt de márgenes internos.
local ANCHO_LINEA = 455
local LETRA = { normal = 5.2, small = 4.7, footnotesize = 4.2 }

local function capacidad(tamano, columnas)
  return (ANCHO_LINEA - 12 * columnas) / LETRA[tamano]
end

-- Largo visible de un elemento y largo del trozo más largo que no se puede cortar.
local function medir(bloques)
  local total, minimo = 0, 0
  local function sumar(largo, cortable)
    total = total + largo
    if not cortable and largo > minimo then minimo = largo end
  end
  pandoc.walk_block(pandoc.Div(bloques), {
    Str = function(e) sumar(utf8.len(e.text) or #e.text, false) end,
    Space = function() total = total + 1 end,
    -- La letra de ancho fijo es más ancha que la normal.
    Code = function(e) sumar(math.ceil(#e.text * 1.25), false) end,
    Math = function(e) sumar(utf8.len(texto_plano(e.text)) or #e.text, false) end,
  })
  return total, minimo
end

-- Separa una fórmula en sus partes unidas por comas de primer nivel (fuera de
-- paréntesis y llaves). Devuelve nil si no hay nada que separar.
local function partes_de_lista(formula)
  local partes, actual, nivel, i = {}, "", 0, 1
  while i <= #formula do
    local resto = formula:sub(i)
    local comando = resto:match("^\\[lr]brace")
    if comando then
      nivel = nivel + (comando == "\\lbrace" and 1 or -1)
      actual = actual .. comando
      i = i + #comando
    else
      local c = formula:sub(i, i)
      if c == "(" or c == "{" then nivel = nivel + 1 end
      if c == ")" or c == "}" then nivel = nivel - 1 end
      if c == "," and nivel == 0 then
        table.insert(partes, actual)
        actual = ""
      else
        actual = actual .. c
      end
      i = i + 1
    end
  end
  table.insert(partes, actual)
  if #partes < 2 then return nil end
  for j, parte in ipairs(partes) do
    partes[j] = parte:gsub("^%s*\\ ", ""):gsub("^%s+", ""):gsub("%s+$", "")
  end
  return partes
end

local separar_listas = {
  Math = function(m)
    if m.mathtype ~= "InlineMath" then return nil end
    local partes = partes_de_lista(m.text)
    if not partes then return nil end
    local salida = {}
    for j, parte in ipairs(partes) do
      if j > 1 then
        table.insert(salida, pandoc.Str(","))
        table.insert(salida, pandoc.Space())
      end
      table.insert(salida, pandoc.Math("InlineMath", parte))
    end
    return salida
  end,
}

function Table(tbl)
  tbl = tbl:walk(separar_listas)
  local n = #tbl.colspecs
  local completo, necesario = {}, {}
  for i = 1, n do completo[i], necesario[i] = 1, 1 end

  local function revisar_filas(filas, es_encabezado)
    for _, fila in ipairs(filas) do
      for i, celda in ipairs(fila.cells) do
        local total, minimo = medir(celda.contents)
        -- Los encabezados pueden partirse en varias líneas.
        if not es_encabezado and total > completo[i] then completo[i] = total end
        if minimo > necesario[i] then necesario[i] = minimo end
      end
    end
  end
  revisar_filas(tbl.head.rows, true)
  for _, cuerpo in ipairs(tbl.bodies) do revisar_filas(cuerpo.body, false) end

  local suma_completo, suma_necesario, holgura = 0, 0, 0
  for i = 1, n do
    if completo[i] < necesario[i] then completo[i] = necesario[i] end
    suma_completo = suma_completo + completo[i]
    suma_necesario = suma_necesario + necesario[i]
    holgura = holgura + (completo[i] - necesario[i])
  end
  if suma_completo <= capacidad("normal", n) then
    -- Cabe tal cual: columnas a su ancho natural.
    for i = 1, n do tbl.colspecs[i] = { tbl.colspecs[i][1], pandoc.ColWidthDefault } end
    return tbl
  end

  -- Letra más chica si lo que no se puede cortar ya ocupa casi toda la línea.
  local tamano = "small"
  if suma_necesario > 0.75 * capacidad("small", n) then tamano = "footnotesize" end
  local cap = capacidad(tamano, n)

  -- Cada columna recibe lo que necesita; lo que sobra se reparte entre las que
  -- pueden partirse en varias líneas, según cuánto texto tienen.
  local sobrante = cap - suma_necesario
  for i = 1, n do
    local ancho
    if sobrante <= 0 then
      ancho = necesario[i] / suma_necesario
    elseif suma_completo <= cap then
      ancho = completo[i] / suma_completo
    else
      ancho = (necesario[i] + sobrante * (completo[i] - necesario[i]) / holgura) / cap
    end
    tbl.colspecs[i] = { tbl.colspecs[i][1], ancho }
  end
  return {
    pandoc.RawBlock("latex", "\\begingroup\\" .. tamano),
    tbl,
    pandoc.RawBlock("latex", "\\endgroup"),
  }
end
