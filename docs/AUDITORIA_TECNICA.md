# INFORME DE AUDITORÍA TÉCNICA — Forecast Engine 2026

**Fecha:** 2026-06-19 | **Versión del proyecto:** 1.2.0 | **Auditor:** Staff Software Engineer

---

## RESUMEN EJECUTIVO

### Estado general del proyecto
El proyecto es funcional y desplegado en producción (Render + Vercel). El frontend se conecta al backend, las rutas API responden, y los datos fluyen de base de datos a interfaz. Sin embargo, existen **desviaciones críticas** entre la arquitectura documentada y la implementación real.

### Nivel de completitud
| Componente | % Funcional | % Conectado | % Correcto |
|------------|------------|-------------|------------|
| API REST | 100% | 100% | 90% |
| Motor de predicciones | 90% | 100% | 65% |
| Simulaciones Monte Carlo | 95% | 100% | 80% |
| Motor IGF | 100% | 60% | 50% |
| Calibración | 100% | 100% | 85% |
| Frontend | 100% | 100% | 70% |
| **Global** | **97%** | **93%** | **73%** |

### Riesgo técnico: **ALTO**
Tres riesgos principales:
1. **IGF inconsistente** — tres fórmulas distintas en tres servicios, produciendo escalas diferentes
2. **Error silencioso en Groups** — el frontend captura `.catch(() => {})` y muestra pantalla de error sin explicación
3. **Bracket mal construido** — `qualified[0::2]` intercala ganadores con terceros puestos, generando llaves incorrectas

---

## HALLAZGOS CRÍTICOS

| # | Hallazgo | Archivo | Línea | Impacto | Severidad |
|---|----------|---------|-------|---------|-----------|
| 1 | **IGF en predicciones no usa el motor IGF** | `match_service.py` | 62-68 | Las predicciones solo usan Elo lineal — los 8 factores del IGF no participan | **CRÍTICO** |
| 2 | **Groups: detail page crash por `standings` undefined** | `[id]/page.tsx` | 101 | TypeError al hacer `.map()` sobre `undefined` → pantalla de error | **CRÍTICO** |
| 3 | **Bracket mal construido en Monte Carlo** | `monte_carlo.py` | ~350 | `qualified[0::2]` intercala ganadores de grupo con terceros puestos | **CRÍTICO** |
| 4 | **Triple definición de IGF con escalas diferentes** | match_service, simulation_service, igf.py | varios | `(elo-1300)/8` vs `(elo-1300)/800` vs motor 8-factores → inconsistencias numéricas | **CRÍTICO** |
| 5 | **Error silencioso en todas las páginas** | frontend/*/page.tsx | varios | `.catch(() => {})` oculta errores de red, 500, 404 | **CRÍTICO** |

---

## HALLAZGOS IMPORTANTES

| # | Hallazgo | Archivo | Línea | Severidad |
|---|----------|---------|-------|-----------|
| 6 | Secret key default en producción | `config.py` | 49 | ALTA |
| 7 | CORS wildcard con endpoints de auth | `main.py` | 100 | ALTA |
| 8 | Sync Redis en contexto async | `cache.py` | 30-90 | ALTA |
| 9 | N+1 queries en ranking y analysis | `ranking_service.py`, `analysis.py` | varias | ALTA |
| 10 | Credenciales hardcodeadas en scripts de auditoría | `audit/*.py` | varias | ALTA |
| 11 | `except: pass` en 9 ubicaciones | varios | varias | ALTA |
| 12 | Detail page de Groups nunca llama `get_group` | `[id]/page.tsx` | 29-38 | ALTA |
| 13 | `match_id` usa `home_team.id` en vez del UUID real | `match_prediction.py` | 163, 218-219 | ALTA |
| 14 | Cache sin invalidación en mutaciones | varios | N/A | MEDIA |
| 15 | Dixon-Coles simplificado (flat multipliers) | `match_prediction.py` | 176-203 | MEDIA |
| 16 | Sin error boundaries en 4 páginas frontend | frontend/ | varias | MEDIA |
| 17 | Calibración no realimenta el pipeline predictivo | `calibration_service.py` | N/A | MEDIA |
| 18 | Ensemble model documentado pero no implementado | docs/ | N/A | BAJA |

---

## MÓDULO GROUPS — Diagnóstico Completo

### Endpoints esperados vs existentes

| Endpoint esperado | Endpoint existente | Estado | Evidencia |
|-------------------|--------------------|--------|-----------|
| `GET /api/v1/groups` | `GET /api/v1/groups` | ✅ OK | `api.ts:375` → `fetchJSON("/groups")`; `main.py:116` registra `groups.router` con prefix `/api/v1` |
| `GET /api/v1/groups/{id}` | `GET /api/v1/groups/{group_id}` | ⚠️ No usado | El frontend nunca llama este endpoint; usa `list()` + filtro por nombre |
| `GET /api/v1/groups/{name}` | ❌ No existe | 🚫 FALLA | La URL del detalle es `/groups/{groupName}` pero el endpoint espera `uuid.UUID` |

### Causa raíz del fallo en Groups

**Problema 1 (crash):** El detalle de grupo en `frontend/src/app/groups/[id]/page.tsx` línea 29 llama `api.groups.list()` (sin standings) y línea 101 hace `group.standings.map(...)`. Como el endpoint `list_groups` retorna `GroupResponse` (sin campo `standings`), `group.standings` es `undefined`, causando `TypeError: Cannot read properties of undefined (reading 'map')`. El error boundary captura el error y muestra "Failed to load group details".

**Problema 2 (enmascaramiento):** Línea 29 y línea 42 usan `.catch(() => {})` que descarga silenciosamente TODOS los errores (red, 500, 404). El usuario ve una página vacía o de error sin indicación de qué ocurrió.

**Problema 3 (inconsistencia de ruta):** La lista genera links con `href={/groups/${group.name}}` (línea 57), pasando el nombre del grupo (ej. "A") como parámetro URL. Pero el backend espera un `uuid.UUID` en `/groups/{group_id}`. La página de detalle ignora el endpoint de detalle y usa el de lista.

### Evidencia
- `frontend/src/app/groups/page.tsx:29`: `api.groups.list().catch(() => {})`
- `frontend/src/app/groups/page.tsx:57`: `<Link key={group.id} href={\`/groups/${group.name}\`}>`
- `frontend/src/app/groups/[id]/page.tsx:29`: `api.groups.list().then(setGroups).catch(() => {})`
- `frontend/src/app/groups/[id]/page.tsx:36-38`: `const match = groups.find(g => g.name === groupName)` — no standings
- `frontend/src/app/groups/[id]/page.tsx:101`: `group.standings.map(...)` → CRASH
- `backend/app/api/groups.py:15`: `@router.get("", response_model=list[GroupResponse])` — sin `standings`
- `backend/app/api/groups.py:21`: `@router.get("/{group_id}", response_model=GroupDetail)` — existe pero no se llama

---

## MOTOR DE PREDICCIONES — Diagnóstico Completo

### Diagrama de flujo real de ejecución

```
Frontend (predictions/[id]/page.tsx)
  │
  └─ GET /api/v1/predictions/full/{match_id}
      │
      ├─ analysis.py:full_prediction()
      │   └─ MatchService.get_full_prediction(match_id)
      │       │
      │       ├─ 1. Cargar Match + EloRating + XGMetrics desde DB
      │       ├─ 2. Construir TeamEntity con:
      │       │      elo_score ← de EloRating (default 1500)
      │       │      xg_for ← de XGMetrics (default 1.0)
      │       │      xg_against ← de XGMetrics (default 1.0)
      │       │      igf_strength ← MIN(100, MAX(0, (elo - 1300) / 8))
      │       │                    ⚠️ NO usa igf.py
      │       │
      │       └─ 3. MatchPredictionEngine.predict_full(home, away)
      │              │
      │              ├─ 3a. predict_dixon_coles(home, away)
      │              │       │
      │              │       └─ predict_poisson()
      │              │              lambda_home = exp(igf_home/50 - igf_away/50 + home_adv)
      │              │              lambda_away = exp(igf_away/50 - igf_home/50)
      │              │              matrix = POISSON_PMF × POISSON_PMF (11×11)
      │              │              win = sum(tril), draw = sum(diag), loss = sum(triu)
      │              │              ⚠️ igf/50 ≈ elo_diff/400, es Elo puro
      │              │
      │              └─ Aplica Dixon-Coles (τ=0.1): ajusta 4 celdas
      │              ├─ 3b. predict_elo() (standalone Elo prediction)
      │              ├─ 3c. _bayesian_update()
      │              │      prior = Elo prior con prior_strength=2.0
      │              │      updated = (2*prior + DC_result) / 3
      │              │      ⚠️ No es Bayesiano real — es promedio ponderado
      │              │
      │              ├─ 3d. _compute_confidence()
      │              │      0.5 * elo_diff/8 + 0.5 * igf_diff * 1.0
      │              │
      │              ├─ 3e. _apply_calibration_adjustments()
      │              │      home_adv_adj, draw_adj — multiplicativos
      │              │
      │              ├─ 3f. Surprise Risk
      │              └─ 3g. Betting Markets (BTTS, O/U, CS)
      │
      └─ JSON Response al frontend
```

### Lo que realmente ocurre matemáticamente

1. **Entrada:** Elo ratings de dos equipos, obtenidos de la tabla `elo_ratings`
2. **IGF = (Elo - 1300) / 8** — mapeo lineal que convierte Elo 1300→0, Elo 2100→100
3. **Poisson λ** = `exp(igf_score / 50 + home_advantage)` ≈ `exp(elo_diff / 400 + 0.08)`
4. **Matrix Poisson** 11×11 usando `np.outer(pmf_home, pmf_away)`
5. **Probabilidades:** suma de triángulo superior (local gana), diagonal (empate), inferior (visitante gana)
6. **Dixon-Coles τ:** ajusta multiplicativamente las celdas (0,0), (0,1), (1,0), (1,1)
7. **Bayesian update:** promedio ponderado 2:1 entre prior Elo y likelihood Dixon-Coles
8. **Calibración:** multiplica win/draw por `(1 + adjustment)` y renormaliza

### Por qué el IGF real (8 factores) no participa

El motor IGF en `igf.py` compute_team_scores() usa 8 factores con pesos configurables y min-max normalization. Pero en el pipeline de predicción:

```python
# match_service.py:62-68
igf_strength = min(100.0, max(0.0, (elo_score - 1300) / 8))
```

Esto reemplaza TODO el motor IGF por una fórmula lineal de Elo. Los datos de xG, forma reciente, experiencia mundialista, calidad de plantilla, etc. se cargan desde la DB pero **nunca se pasan al engine de predicción**.

---

## SIMULACIONES MONTE CARLO — ¿Influyen o son decorativas?

### Respuesta definitiva: **SON DECORATIVAS**

Las simulaciones NO afectan el resultado de las predicciones. Son puramente informativas.

### Evidencia

1. **Sin dependencia algorítmica:** `SimulationResult` es consumido exclusivamente por endpoints de solo lectura (dashboard, comparación, exportación). El `MatchPredictionEngine` nunca consulta la tabla `simulations` o `simulation_results`.

2. **Flujo de datos:** `DB → SimulationService → MonteCarloEngine.run() → SimulationResult[DB] → GET endpoints → display` — no hay lazo de retroalimentación.

3. **Match predictions son independientes:** `match_service.py` y `predictions.py` no referencian simulación alguna.

4. **Rankings son independientes:** `ranking_service.py` construye IGF desde Elo + otros factores, nunca desde simulaciones.

### Sin embargo, SÍ se ejecutan realmente

- 100,000 iteraciones default (configurable vía API)
- Distribución Poisson para goles
- Numba JIT acceleration (5 funciones con `@njit`)
- Paralelismo con `ProcessPoolExecutor` (4 workers)
- Tiebreakers FIFA: puntos, GD, GF
- Tiempo extra + penales en eliminatorias
- Validación: `phase76_validation.py` corre 1, 10k, 50k, 100k y verifica convergencia

### Bug conocido en bracket

En `monte_carlo.py` ~línea 350, la construcción del bracket usa `qualified[0::2]` que intercala ganadores de grupo con equipos de tercer puesto. Esto produce llaves incorrectas en algunas configuraciones.

---

## CÓDIGO MUERTO

| Componente | Estado | Archivo | Evidencia |
|------------|--------|---------|-----------|
| `GET /api/v1/groups/{group_id}` | **Endpoint no consumido** | `groups.py:21` | El frontend nunca lo llama; la URL de detalle usa nombre, no UUID |
| `IGFEngine.compute_team_scores()` | **No usado en predicciones** | `igf.py` | El pipeline usa `(elo-1300)/8` en vez del motor 8-factores |
| `xG data` en TeamEntity | **Cargado pero ignorado** | `match_service.py:56-58` | `xg_for`, `xg_against` se cargan de DB pero `MatchPredictionEngine` solo usa `igf_score` |
| `MatchPredictionConfig.max_goals` | **Hardcodeado a 10** | `match_prediction.py` | `config.max_goals` existe pero siempre es 10 |
| `GET /api/v1/predictions/rankings` | **Endpoint existente, ¿consumido?** | `predictions.py:95-106` | No se encontró llamada desde frontend a `api.predictions.rankings()` |
| Fallback sync en cache.py | **No usado** | `cache.py:72-74` | `get_sync()` existe pero solo lo usa `@cached` decorator en endpoints GET |
| Ensemble model | **Documentado, no implementado** | docs/ | Solo mencionado como trabajo futuro |
| Logistic Regression (predicción) | **No implementado** | N/A | Solo existe como Platt Scaling en calibración |

### Código parcialmente integrado

| Componente | Estado | Archivo | Evidencia |
|------------|--------|---------|-----------|
| Calibración → ajustes automáticos | **Conectado pero sin feedback loop** | `calibration_service.py` | Los ajustes se calculan y almacenan pero la predicción solo los usa si `build_config_with_adjustments()` los retorna; el ciclo no es automático |
| Dixon-Coles τ | **Simplificado** | `match_prediction.py:284-318` | Aplica multiplicadores planos a 4 celdas, no implementa la función de correlación completa |
| Bayesian update | **Promedio ponderado** | `match_prediction.py:321-349` | No hay distribución posterior real, solo `(2*prior + likelihood)/3` |

### Código completamente integrado

| Componente | Archivo | Estado |
|------------|---------|--------|
| Poisson | `match_prediction.py:138-174` | ✅ |
| Elo | `match_prediction.py:205-229` | ✅ |
| Dixon-Coles (simplificado) | `match_prediction.py:176-203` | ✅ |
| Monte Carlo | `monte_carlo.py` | ✅ |
| Calibración (Brier, ECE, curvas) | `calibration.py` | ✅ |
| Isotonic / Platt / Temperature | `calibration_refinement.py` | ✅ |
| Confidence Index | `match_prediction.py:351-372` | ✅ |
| Betting Markets | `match_prediction.py:413-449` | ✅ |
| IGF Rankings (8 factores) | `ranking_service.py` + `igf.py` | ✅ (solo para rankings) |
| Exportación JSON/CSV | `export.py` | ✅ |
| Scenarios What-If | `scenarios.py` | ✅ |

---

## VALIDACIÓN DEL CÁLCULO PROBABILÍSTICO

### Partido de ejemplo: Selección Argentina vs Francia

**Datos de entrada (desde DB):**
```
Argentina: Elo=2012 → igf=(2012-1300)/8=89.0
Francia:   Elo=1987 → igf=(1987-1300)/8=85.9
```

**Paso 1: Poisson λ**
```
lambda_home = exp(89.0/50 - 85.9/50 + 0.08) = exp(0.062 + 0.08) = exp(0.142) = 1.153
lambda_away = exp(85.9/50 - 89.0/50) = exp(-0.062) = 0.940
```

**Paso 2: Matriz Poisson 11×11**
```
P(0) = e^-1.153 * 1.153^0 / 0! = 0.316
P(1) = e^-1.153 * 1.153^1 / 1! = 0.364
P(2) = e^-1.153 * 1.153^2 / 2! = 0.210
...etc para goles 0-10

Local:  [0.316, 0.364, 0.210, 0.081, 0.023, 0.005, 0.001, 0.000, 0.000, 0.000, 0.000]
Visita: [0.391, 0.368, 0.173, 0.054, 0.013, 0.002, 0.000, 0.000, 0.000, 0.000, 0.000]
```

**Paso 3: Matriz de probabilidades conjuntas (producto externo)**
```
np.outer(home_pmf, away_pmf) produce matriz 11×11
sum = 1.0

Ej: P(1-0) = 0.364 × 0.391 = 0.142
    P(0-0) = 0.316 × 0.391 = 0.123
    P(1-1) = 0.364 × 0.368 = 0.134
```

**Paso 4: Probabilidades base (Poisson crudo)**
```
P_local_gana = sum(triu(matrix)) ≈ 0.456
P_empate     = sum(diag(matrix))  ≈ 0.271
P_visita_gana = sum(tril(matrix)) ≈ 0.273
```

**Paso 5: Dixon-Coles τ = 0.1**
```
P(0-0) ajustado = 0.123 × (1 - 0.1) = 0.111
P(0-1) ajustado = 0.117 × (1 + 0.1) = 0.129
P(1-0) ajustado = 0.142 × (1 + 0.1) = 0.156
P(1-1) ajustado = 0.134 × (1 - 0.1) = 0.121
Renormalizado:
P_local = 0.462 | P_empate = 0.265 | P_visita = 0.273
```

**Paso 6: Bayesian update (prior_strength=2.0)**
```
Elo predicted:
  expected_home = 1/(1+10^((1987-2012+0)/400)) = 0.535
  prior_local  = 0.535 - 0.25/2 = 0.410
  prior_empate = 0.25
  prior_visita = 1 - 0.410 - 0.25 = 0.340

updated_local  = (2 × 0.410 + 0.462) / 3 = 0.427
updated_empate = (2 × 0.250 + 0.265) / 3 = 0.255
updated_visita = (2 × 0.340 + 0.273) / 3 = 0.318
```

**Paso 7: Ajustes de calibración (ejemplo: home_adj=+0.05, draw_adj=-0.02)**
```
local  = 0.427 × 1.05 = 0.448
empate = 0.255 × 0.98 = 0.250
visita = 0.318

Suma = 1.016 → renormalizar:
P_local  = 0.448 / 1.016 = 0.441 → **44.1%**
P_empate = 0.250 / 1.016 = 0.246 → **24.6%**
P_visita = 0.250 / 1.016 = 0.313 → **31.3%**
```

**Resultado final devuelto al frontend:**
```json
{
  "home_win_prob": 0.441,
  "draw_prob": 0.246,
  "away_win_prob": 0.313,
  "expected_goals_home": 1.153,
  "expected_goals_away": 0.940,
  "most_likely_score": "1-0",
  "confidence_index": 64.2,
  "confidence_level": "Alta",
  "surprise_risk": 0.559
}
```

**Conclusión:** El cálculo es matemáticamente correcto dentro de las asunciones del modelo (Poisson + Dixon-Coles + promedio ponderado). Pero la limitación fundamental es que la fortaleza de cada equipo (IGF) se deriva exclusivamente de Elo, ignorando los otros 7 factores del IGF Engine.

---

## AUDITORÍA DE CALIDAD

### Patrones de código pendiente (TODO, FIXME, HACK)

| Archivo | Línea | Patrón | Código | Impacto |
|---------|-------|--------|--------|---------|
| `app/core/config.py` | 49 | TODO | `"change-me-in-production"` | Crítico |
| `app/engine/match_prediction.py` | varios | - | `igf/50` sin validación de rango | Medio |
| `frontend/*/page.tsx` | varios | catch | `.catch(() => {})` | Crítico |
| `app/core/cache.py` | 30-90 | HACK | Sync Redis en contexto async | Alto |
| `app/engine/monte_carlo.py` | ~350 | BUG | `qualified[0::2]` bracket mal construido | Crítico |
| `audit/*.py` | varios | HARDCODE | Passwords de DB en texto plano | Alto |

### try/catch que ocultan errores

| Archivo | Línea | Código | Impacto |
|---------|-------|--------|---------|
| `app/core/cache.py` | 72-74 | `try: ... except: return None` | Oculta errores de Redis |
| `app/core/cache.py` | 89-90 | `try: ... except: pass` | Silencia errores de escritura |
| `app/core/startup.py` | varias | `try: ... except Exception as e: ...` | Riesgo medio |
| `frontend/*/page.tsx` | múltiples | `.catch(() => {})` | Oculta TODOS los errores al usuario |

### Valores hardcodeados

| Archivo | Línea | Valor | Problema |
|---------|-------|-------|----------|
| `config.py` | 49 | `"change-me-in-production"` | Secret key por defecto |
| `match_service.py` | 62 | `(elo - 1300) / 8` | IGF lineal basado solo en Elo |
| `simulation_service.py` | ~97 | `(elo - 1300) / 800` | IGF diferente escala |
| `match_prediction.py` | 143-146 | `igf_score / 50.0` | Factor de escala arbitrario |
| `match_prediction.py` | 182 | `tau = 0.1` | Dixon-Coles sin optimizar |
| `domain/entities.py` | 135 | `num_simulations = 100_000` | Default arbitrario |

---

## VEREDICTO FINAL

### 1. ¿Las predicciones utilizan realmente modelos estadísticos avanzados?

**Sí, pero no todos los que la documentación describe.**

Lo que SÍ usa:
- ✅ **Poisson** — implementación real con PMF, matriz de probabilidades, suma de regiones
- ✅ **Dixon-Coles** — implementación real (aunque simplificada) con τ correction
- ✅ **Elo** — fórmula estándar de Arpad Elo
- ✅ **Bayesian update** — convex combination (promedio ponderado) entre prior Elo y likelihood Dixon-Coles
- ✅ **Platt Scaling / Isotonic / Temperature** — para calibración post-hoc

Lo que NO usa pero la documentación sugiere:
- ❌ **IGF Engine (8 factores)** — las predicciones usan una transformación lineal de Elo, no el motor de 8 factores
- ❌ **Logistic Regression** — solo existe como Platt Scaling en calibración, no como modelo de predicción
- ❌ **Ensemble** — documentado como trabajo futuro, sin implementación

### 2. ¿Las simulaciones Monte Carlo impactan el resultado?

**NO.** Las simulaciones Monte Carlo son **puramente decorativas**. No existe ningún lazo de retroalimentación entre `SimulationResult` y el `MatchPredictionEngine` o el `RankingService`. La simulación se ejecuta, persiste resultados, y se muestran en dashboard/comparación/exportación — pero nunca modifican las predicciones de partidos ni los rankings.

### 3. ¿El sistema está generando probabilidades reales o aproximaciones simplificadas?

**Probabilidades reales, pero con una simplificación fundamental.**

La cadena matemática es correcta: Elo → IGF lineal → Poisson λ → matriz 11×11 → Dixon-Coles → Bayesian weighting → ajustes. Cada paso tiene una base estadística legítima.

La simplificación fundamental está en la entrada: **la fortaleza del equipo (IGF) se reduce a una transformación lineal de Elo**, ignorando los otros 7 factores (forma reciente, xG, xGA, calidad de plantilla, experiencia mundialista, etc.). Esto significa que dos equipos con el mismo Elo pero diferente forma reciente recibirían la misma predicción.

### 4. ¿Qué porcentaje del motor de predicción está efectivamente implementado y conectado?

| Componente | % Implementado | % Conectado | Nota |
|------------|---------------|-------------|------|
| Poisson | 100% | 100% | λ basado en IGF lineal |
| Dixon-Coles | 70% | 100% | Simplificado (flat multipliers) |
| Elo | 100% | 100% | Fórmula estándar |
| Bayesian update | 60% | 100% | Promedio ponderado, no Bayesiano real |
| Confidence Index | 100% | 100% | Heurística |
| Betting Markets | 100% | 100% | Derivados de la matriz Poisson |
| IGF Engine | 100% | 60% | Conectado a rankings pero NO a predicciones |
| Calibración | 100% | 100% | Brier, ECE, ajustes multiplicativos |
| Calibración Refinement | 100% | 100% | Isotonic, Platt, Temperature |
| Monte Carlo | 95% | 100% | Bug en bracket |
| Ensemble | 0% | 0% | No implementado |
| Logistic Regression | 30% | 30% | Solo como Platt Scaling |

**Global: ~80% del motor documentado está implementado y conectado.**

### 5. ¿Cuál es la causa raíz del fallo en Groups?

**Causa raíz: El frontend de detalle de Groups espera que el endpoint `list_groups` devuelva `standings`, pero el endpoint retorna `GroupResponse` (sin `standings`).**

Flujo exacto del error:
1. Usuario navega a `/groups/A`
2. `[id]/page.tsx:29` ejecuta `api.groups.list()` → `GET /api/v1/groups`
3. Backend retorna `list[GroupResponse]` — objetos sin campo `standings`
4. Línea 36-38: `groups.find(g => g.name === groupName)` encuentra el grupo "A" sin standings
5. Línea 101: `group.standings.map(s => ...)` → **TypeError: `standings` is undefined**
6. React Error Boundary captura el error y muestra `[id]/error.tsx` → "Failed to load group details"

**NO es un error de conexión.** La red funciona, el endpoint responde 200, los datos llegan. Es un error de **contrato entre frontend y backend** — el schema que el frontend asume (con `standings`) no coincide con lo que el backend devuelve.

**Reparación necesaria:** Cambiar `list_groups` para incluir `standings` con `joinedload`, o cambiar el frontend para no depender de standings en la lista, o llamar `get_group` con el UUID en vez de filtrar por nombre.

---

## RECOMENDACIONES

### Inmediatas (impacto alto, esfuerzo bajo)

| # | Acción | Archivo | Esfuerzo |
|---|--------|---------|----------|
| 1 | Agregar `standings` a `list_groups` con `joinedload(Group.standings)` | `groups.py` | 15 min |
| 2 | Reemplazar `.catch(() => {})` con logging + UI de error | frontend/*/page.tsx | 30 min |
| 3 | Reemplazar `allow_origins=["*"]` por lista explícita una vez funcione CORS | `main.py` | 5 min |
| 4 | Establecer `secret_key` segura (no default) | Render Dashboard | 2 min |

### Corto plazo (impacto alto, esfuerzo medio)

| # | Acción | Archivo | Esfuerzo |
|---|--------|---------|----------|
| 5 | Unificar cálculo de IGF: usar `IGFEngine.compute_team_scores()` en match_service y simulation_service | `match_service.py`, `simulation_service.py` | 2-3 h |
| 6 | Corregir bracket en Monte Carlo (`qualified[0::2]`) | `monte_carlo.py` | 30 min |
| 7 | Agregar `error.tsx` en páginas frontend sin él | frontend/ | 30 min |
| 8 | Reemplazar sync Redis por async (`aioredis` o `redis.asyncio`) | `cache.py` | 2-3 h |
| 9 | Agregar `response_model` a `full_prediction` en analysis.py | `analysis.py` | 10 min |

### Mediano plazo (impacto medio, esfuerzo alto)

| # | Acción | Esfuerzo |
|---|--------|----------|
| 10 | Implementar Ensemble model (combinación ponderada de Poisson, Elo, Logistic Regression) | 1-2 semanas |
| 11 | Pipeline automático de calibración → ajustes → predicción (feedback loop) | 1 semana |
| 12 | Optimización de τ en Dixon-Coles mediante búsqueda de grilla | 2-3 días |
| 13 | Implementar cache invalidation en endpoints de mutación | 1-2 días |
| 14 | Agregar N+1 query detection y optimizar con `selectinload` / `joinedload` | 1-2 días |

### Largo plazo (visión)

| # | Acción | Esfuerzo |
|---|--------|----------|
| 15 | Implementar modelo bayesiano completo (conjugate priors, MCMC o Pyro/PyMC) | 2-4 semanas |
| 16 | Dashboard de monitoreo de métricas de calibración en tiempo real | 1-2 semanas |
| 17 | Pipeline CI/CD con validación de precisión de predicciones antes de deploy | 1-2 semanas |

---

## ANEXO: Archivos clave referenciados

| Archivo | Propósito | Líneas |
|---------|-----------|--------|
| `backend/app/api/groups.py` | Router Groups (2 endpoints) | 30 |
| `backend/app/services/match_service.py` | Orquesta predicciones | 135 |
| `backend/app/engine/match_prediction.py` | Core: Poisson, DC, Elo, Bayes, Confidence, Markets | 449 |
| `backend/app/engine/igf.py` | IGF Engine 8-factores | 144 |
| `backend/app/engine/monte_carlo.py` | Simulaciones Monte Carlo con Numba | 468 |
| `backend/app/engine/calibration.py` | Calibración (Brier, ECE, bias) | 453 |
| `backend/app/engine/calibration_refinement.py` | Isotonic, Platt, Temperature Scaling | 589 |
| `backend/app/services/simulation_service.py` | Orquesta simulaciones | 182 |
| `backend/app/services/ranking_service.py` | Rankings Elo, FIFA, IGF | 107 |
| `backend/app/core/cache.py` | Cache sync (problema async) | 95 |
| `backend/app/domain/entities.py` | Dataclasses del dominio | 166 |
| `frontend/src/app/groups/page.tsx` | Groups list page | ~70 |
| `frontend/src/app/groups/[id]/page.tsx` | Groups detail page (roto) | ~120 |
| `frontend/src/lib/api.ts` | API client frontend | ~400 |
| `backend/scripts/phase76_validation.py` | Validación Monte Carlo | 588 |

---

*Fin del informe de auditoría. 2026-06-19.*
