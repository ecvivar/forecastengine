# Manual de Usuario — WorldCup Forecast Engine 2026

**Versión:** 1.0 | **Fecha:** 2026-06-11

Plataforma profesional de pronóstico y simulación para la Copa Mundial de la FIFA 2026. Genera predicciones de partidos, clasificaciones de grupo y torneos completos mediante métodos Monte Carlo con más de 100.000 iteraciones.

---

## Índice

1. [Acceso a la Plataforma](#1-acceso-a-la-plataforma)
2. [Navegación General](#2-navegación-general)
3. [Dashboard (Inicio)](#3-dashboard-inicio)
4. [Equipos](#4-equipos)
5. [Comparación de Equipos](#5-comparación-de-equipos)
6. [Grupos](#6-grupos)
7. [Fase Eliminatoria](#7-fase-eliminatoria)
8. [Bracket del Torneo](#8-bracket-del-torneo)
9. [Explorador del Torneo](#9-explorador-del-torneo)
10. [Partidos](#10-partidos)
11. [Predicciones de Partidos](#11-predicciones-de-partidos)
12. [Rankings y Power Rankings](#12-rankings-y-power-rankings)
13. [Escenarios (What-If)](#13-escenarios-what-if)
14. [Exportación de Datos](#14-exportación-de-datos)
15. [Reportes Ejecutivos](#15-reportes-ejecutivos)
16. [Simulaciones Monte Carlo](#16-simulaciones-monte-carlo)
17. [Calibración del Modelo](#17-calibración-del-modelo)
18. [Glosario](#18-glosario)
19. [Preguntas Frecuentes](#19-preguntas-frecuentes)

---

## 1. Acceso a la Plataforma

| Entorno | URL |
|---------|-----|
| **Producción** | [https://forecastengine-tau.vercel.app](https://forecastengine-tau.vercel.app) |
| **API (Swagger UI)** | [https://forecastengine-yq39.onrender.com/docs](https://forecastengine-yq39.onrender.com/docs) |

No requiere registro ni autenticación — toda la información es de acceso público.

---

## 2. Navegación General

La barra de navegación superior contiene enlaces a todas las secciones:

```
[WC26 Forecast Engine]  Dashboard  Teams  Comparison  Groups  Knockout
Bracket  Explorer  Matches  Predictions  Rankings  Scenarios  Export
Reports  Simulations  Calibration
```

En dispositivos móviles, la navegación se colapsa en un menú tipo hamburguesa.

---

## 3. Dashboard (Inicio)

El dashboard es la página principal y ofrece una vista general del torneo.

### Componentes

1. **Tarjetas de resumen** — Muestran métricas clave:
   - Total de equipos (48)
   - Total de grupos (12)
   - Total de partidos
   - Partidos de fase de grupos
   - Partidos de eliminación directa

2. **Top 10 Equipos por IGF** — Los 10 equipos con mayor Índice de Fuerza Global (IGF), ordenados de mayor a menor. Cada entrada muestra:
   - Posición en el ranking
   - Nombre del equipo y código FIFA
   - Continente
   - Puntaje IGF (0-100)
   - Puntaje Elo

3. **Probabilidades de Campeón** — Para los 8 principales contendientes, muestra el porcentaje de probabilidad de ganar el torneo, llegar a la final, llegar a semifinales y llegar a cuartos de final.

4. **Resumen de Grupos** — Tarjetas de cada grupo con los 4 equipos, su posición actual y puntos. Al hacer clic en una tarjeta, se navega al detalle del grupo.

5. **Predicciones Recientes** — Tabla de los próximos 10 partidos con predicciones:
   - Equipo local y visitante
   - Resultado más probable
   - Probabilidad de victoria local, empate, victoria visitante
   - Índice de confianza
   - Nivel de confianza
   - Riesgo de sorpresa

---

## 4. Equipos

Lista completa de las 48 selecciones participantes.

- **Búsqueda:** Filtro por nombre de equipo.
- **Tarjetas:** Cada equipo muestra código FIFA, continente y puntaje IGF.
- **Radar IGF:** Al hacer clic en un equipo, se abre un gráfico radial con los componentes del IGF:
  - Elo
  - Forma reciente
  - xG (goles esperados)
  - xGA (goles esperados en contra)
  - Fortaleza del oponente
  - Experiencia en mundiales
  - Calidad de la plantilla

---

## 5. Comparación de Equipos

Herramienta de comparación cara a cara entre dos selecciones.

1. Seleccionar **Equipo A** y **Equipo B** desde los menús desplegables.
2. La plataforma muestra:
   - **Ranking Elo** comparativo
   - **Índice IGF** comparativo
   - **Ranking FIFA** comparativo
   - Estadísticas de grupo
   - Métricas de goles esperados (xG)
   - Pronóstico del enfrentamiento directo con barra de probabilidad
   - **Proyección de torneo:** probabilidades de cada equipo para cada etapa (R32, R16, QF, SF, Final, Campeón)

---

## 6. Grupos

Vista general de los 12 grupos (A–L) del Mundial 2026.

### Vista General

Cada grupo muestra:
- Nombre del grupo
- Tabla de posiciones: posición, equipo, PJ (partidos jugados), G (ganados), E (empatados), P (perdidos), GF (goles a favor), GA (goles en contra), GD (diferencia de gol), Pts (puntos)
- Indicador visual de clasificación (equipos clasificados vs eliminados)

### Detalle de Grupo (`/groups/[id]`)

Al hacer clic en un grupo:
- Tabla de posiciones completa
- **Probabilidades de clasificación:** para cada equipo, barras de progreso que muestran la probabilidad de avanzar a cada etapa (R32, R16, QF, SF, Final, Campeón), basadas en simulaciones Monte Carlo

---

## 7. Fase Eliminatoria

Probabilidades de la fase eliminatoria organizadas en tres pestañas:

| Pestaña | Contenido |
|---------|-----------|
| **Campeón** | Podio (top 3) con probabilidad de ganar el torneo, más tabla completa de todos los equipos |
| **Final** | Podio con probabilidad de llegar a la final, más tabla completa |
| **Semifinal** | Podio con probabilidad de llegar a semifinales, más tabla completa |

Cada tabla incluye para cada equipo la probabilidad de avanzar a cada etapa:
R32 → R16 → QF → SF → Final → Campeón

Al final, un gráfico de **perfiles de avance** para los 16 mejores equipos muestra visualmente la probabilidad acumulada en cada etapa.

---

## 8. Bracket del Torneo

Visualización del bracket proyectado del torneo, desde octavos de final (R32) hasta la final.

- Muestra el **campeón proyectado** con su escudo y nombre
- Para cada equipo en el bracket, muestra probabilidades:
  - Ganar el torneo
  - Llegar a la final
  - Llegar a semifinales
  - Llegar a cuartos de final
  - Llegar a octavos de final

---

## 9. Explorador del Torneo

Tres vistas en pestañas para explorar el torneo desde diferentes ángulos:

| Pestaña | Descripción |
|---------|-------------|
| **Fase de Grupos** | Probabilidades de clasificación por grupo. Para cada grupo, muestra la probabilidad de cada equipo de avanzar a la fase eliminatoria |
| **Probabilidades Eliminatorias** | Tabla completa ordenable con todos los equipos y sus probabilidades etapa por etapa |
| **Trayectoria de Equipo** | Seleccioná un equipo específico para ver su probabilidad de avance etapa por etapa y los oponentes en su grupo |

---

## 10. Partidos

Lista completa de los 104 partidos del torneo (fase de grupos + eliminatorias).

- **Filtro por etapa:** Fase de grupos, R32, R16, Cuartos, Semifinal, Final
- Cada partido muestra:
  - Fecha
  - Grupo (si aplica)
  - Equipo local vs. Equipo visitante
  - Marcador (si ya se jugó)
  - Insignia de estado (Programado, En vivo, Finalizado)

---

## 11. Predicciones de Partidos

### Vista General (`/predictions`)

Grilla de tarjetas de predicción para todos los partidos. Cada tarjeta incluye:
- Equipo local y visitante
- Resultado más probable (ej. 2-1)
- Goles esperados (xG) para cada equipo
- Barra de probabilidad: victoria local / empate / victoria visitante
- Índice de confianza (0-100)
- Riesgo de sorpresa (bajo, medio, alto)

### Detalle de Predicción (`/predictions/[id]`)

Al hacer clic en una predicción, se abre una vista detallada con:

1. **Probabilidades de resultado** — Barra detallada con porcentajes exactos
2. **Indicador de confianza** — Medidor visual del nivel de confianza en la predicción
3. **Riesgo de sorpresa** — Evaluación de qué tan probable es un resultado inesperado
4. **Marcadores más probables** — Top 10 resultados con sus probabilidades, mostrados en un gráfico de barras (ScorelineChart)
5. **Mercados de apuestas:**
   - Ambos equipos anotan (BTTS) — Sí/No con probabilidad
   - Más/Menos de 2.5 goles
   - Más/Menos de 3.5 goles
   - Valla invicta (clean sheet) para cada equipo

---

## 12. Rankings y Power Rankings

Tres pestañas:

### IGF Rankings

Tabla completa ordenable con todos los equipos y su desglose IGF:
- **IGF Score:** Puntaje compuesto (0-100)
- **Elo:** Rating Elo
- **Form:** Forma reciente
- **xG:** Goles esperados
- **xGA:** Goles esperados en contra
- **Squad:** Calidad de la plantilla

### Power Ranking

Clasificación de equipos en categorías según su nivel:
- **Contendientes al título** — Los equipos con mayor probabilidad de ganar el torneo
- **Candidatos a semifinales** — Equipos con potencial para llegar lejos
- **Candidatos a cuartos de final** — Equipos de nivel intermedio-alto
- **Posible eliminación temprana** — Equipos con menor proyección

### Vista Radar

Seleccioná un equipo para ver su gráfico radial con los 7 componentes del IGF.

---

## 13. Escenarios (What-If)

Herramienta de análisis de escenarios. Permite modificar la fortaleza de los equipos y ver cómo cambian las probabilidades.

### Cómo usar

1. Seleccioná uno o más equipos
2. Ajustá el **modificador de fortaleza** (porcentaje, positivo o negativo)
   - Ejemplo: +10% hace al equipo un 10% más fuerte
   - Ejemplo: -15% simula la ausencia de un jugador clave
3. Configurá el **número de simulaciones** (100 a 10,000)
4. Hacé clic en **"Run Scenario"**
5. La tabla de resultados muestra:
   - **Baseline:** Probabilidad original (sin modificadores)
   - **Resultado:** Nueva probabilidad con los modificadores aplicados
   - **Delta:** Diferencia (puntos porcentuales) — color verde si mejora, rojo si empeora

---

## 14. Exportación de Datos

Centro de exportación para descargar datos en formato JSON o CSV.

### Formatos disponibles

| Tipo | Formato | Contenido |
|------|---------|-----------|
| Equipos | JSON | Perfiles completos de los 48 equipos |
| Grupos | JSON | Tablas de posiciones de todos los grupos |
| Simulaciones | JSON | Resultados completos de simulaciones Monte Carlo |
| Rankings Elo | JSON | Rankings Elo históricos |
| Rankings FIFA | JSON | Rankings FIFA oficiales |
| Rankings IGF | JSON | Índice de Fuerza Global con todos los componentes |
| Partidos | CSV | Todos los partidos con resultados y predicciones |
| Simulaciones | CSV | Resultados de simulación en formato tabular |

---

## 15. Reportes Ejecutivos

Panel de reportes con un resumen ejecutivo del torneo:

- **Principales contendientes** — Los equipos con mayor probabilidad de ganar
- **Caballos negros** — Equipos con bajo perfil pero alta probabilidad de sorprender
- **Final más probable** — El enfrentamiento de final con mayor probabilidad según las simulaciones
- **Tarjetas de insight del torneo** — Datos curiosos y estadísticas destacadas
- **Distribución de IGF** — Gráfico de distribución de puntajes IGF entre todos los equipos
- **Sección de ideas clave** — Análisis y conclusiones generadas por el sistema

---

## 16. Simulaciones Monte Carlo

### Lista de Simulaciones (`/simulations`)

Muestra todas las simulaciones ejecutadas con:
- Nombre de la simulación
- Número de iteraciones (ej. 100,000)
- Estado: **En progreso** (spinner) o **Completado** (checkmark)
- Fecha de finalización
- Campeón proyectado

**Nueva simulación:** Botón para ejecutar una simulación rápida de 10,000 iteraciones.

### Detalle de Simulación (`/simulations/[id]`)

Al abrir una simulación:
- **Encabezado:** Nombre, iteraciones, fecha, equipo campeón proyectado
- **Podio:** Top 3 (Campeón, segundo lugar, tercer lugar)
- **Histograma:** Distribución de probabilidad de campeón para los principales contendientes
- **Tabla de resultados completa:**
  - Equipo
  - Probabilidad de ganar el torneo
  - Probabilidad de llegar a cada ronda (R32, R16, QF, SF, Final)
  - Puntos promedio

---

## 17. Calibración del Modelo

Panel de análisis de calibración del modelo de predicción. Muestra qué tan bien calibradas están las predicciones del sistema.

### Métricas

| Métrica | Descripción | Valor |
|---------|-------------|-------|
| **Brier Score** | Error cuadrático medio de las predicciones (menor = mejor) | Ej. 0.18 |
| **ECE** | Error de calibración esperado (menor = mejor) | Ej. 0.05 |
| **Accuracy** | Precisión general de las predicciones | Ej. 68% |
| **Mejor método** | Método de calibración óptimo según los datos | Ej. "Platt Scaling" |

### Componentes

1. **Curva de calibración** — Gráfico que muestra qué tan bien calibradas están las predicciones (ideal = línea diagonal)
2. **Comparativa de benchmarks** — Rendimiento antes y después de la calibración
3. **Tabla comparativa de modelos** — Comparación de diferentes modelos de predicción
4. **Métodos de calibración** — Tabla con los diferentes métodos probados y su rendimiento
5. **Diagramas de confiabilidad** — Gráficos de confiabilidad para cada método
6. **Reducción de sesgo** — Resultados de la reducción de sesgo en las predicciones
7. **Recomendación** — Tarjeta con el método de calibración recomendado

---

## 18. Glosario

| Término | Definición |
|---------|------------|
| **IGF (Índice de Fuerza Global)** | Puntaje compuesto (0-100) que mide la fortaleza general de un equipo. Combina Elo, forma reciente, xG, xGA, fortaleza del oponente, experiencia mundialista y calidad de plantilla |
| **Elo** | Sistema de rating basado en resultados históricos. Cada equipo parte de 1500 puntos y gana/pierde según el resultado de cada partido |
| **xG (Goles Esperados)** | Métrica que mide la calidad de las oportunidades de gol creadas por un equipo. Un tiro desde el punto penal vale ~0.79 xG, uno desde media distancia ~0.05 xG |
| **xGA (Goles Esperados en Contra)** | Versión defensiva del xG — mide la calidad de las oportunidades de gol que un equipo concede al rival |
| **Monte Carlo** | Método de simulación que ejecuta miles de iteraciones del torneo completo, cada una con resultados probabilísticos, para calcular probabilidades agregadas |
| **Brier Score** | Medida de precisión de predicciones probabilísticas. Va de 0 (perfecto) a 1 (pésimo) |
| **Platt Scaling** | Técnica de calibración que ajusta las probabilidades crudas del modelo para que reflejen mejor las frecuencias observadas |
| **BTTS (Both Teams To Score)** | Mercado de apuestas que predice si ambos equipos anotarán al menos un gol |
| **R32, R16, QF, SF** | Abreviaturas de las rondas: Round of 32 (octavos), Round of 16 (cuartos de final olímpico), Quarter-Finals (cuartos de final), Semi-Finals (semifinales) |

---

## 19. Preguntas Frecuentes

### ¿Cómo se generan las predicciones?

Las predicciones combinan múltiples modelos estadísticos (Poisson, Dixon-Coles, Elo, Bayesiano) con el Índice de Fuerza Global (IGF) de cada equipo. Los resultados se calibran contra datos históricos para maximizar la precisión.

### ¿Qué precisión tienen las predicciones?

El sistema se calibra continuamente usando datos de partidos históricos. Las métricas de calibración (Brier Score, ECE, Accuracy) están disponibles en la sección **Calibration**.

### ¿Cómo funciona la simulación Monte Carlo?

El motor ejecuta más de 100,000 simulaciones del torneo completo. En cada simulación:
1. Se determinan los resultados de la fase de grupos usando modelos de probabilidad
2. Se avanza a través de las rondas eliminatorias (R32 → R16 → QF → SF → Final)
3. Se registra qué equipo ganó y hasta dónde llegó cada uno
4. Al final, se agregan los resultados de todas las simulaciones para calcular probabilidades

### ¿Cada cuánto se actualizan los datos?

Los datos se actualizan en cada depliegue del backend. Las fuentes incluyen FIFA, Elo Ratings, FBref y Transfermarkt.

### ¿Puedo usar estos datos para apuestas?

Esta plataforma es solo para fines informativos y educativos. Las predicciones no garantizan resultados reales. Apostar conlleva riesgos financieros.

### ¿Los escenarios What-If son persistentes?

No. Los escenarios se ejecutan en memoria y los resultados se muestran en la misma sesión. No se guardan en la base de datos.

### ¿Cómo exportar los datos?

Usá la sección **Export** para descargar datos en formato JSON o CSV. Cada exportación incluye todos los registros disponibles.

### ¿La plataforma es gratuita?

Sí, la plataforma es de acceso público y gratuito. No requiere registro.

---

*WorldCup Forecast Engine 2026 — Proyecto de código abierto. Documentación generada el 2026-06-11.*
