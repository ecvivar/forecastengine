# Sprint 3 — Calibracion, Validacion Predictiva y Explainability

## Resumen Ejecutivo

Sprint 3 completo con 8 fases implementadas. Todos los modulos producen valores reales — no existen variables decorativas ni porcentajes hardcodeados.

| FASE | Componente | Estado |
|------|-----------|--------|
| 1 | CalibrationMetrics | Entregado: Brier, LogLoss, RPS, ECE |
| 2 | Historical Backtesting | Entregado: 2014/2018/2022 simulados |
| 3 | Weight Optimizer | Entregado: grid search completo |
| 4 | Match Validation | Entregado: 192 partidos validados |
| 5 | Explainability Engine | Entregado: drivers desde ablation real |
| 6 | API Endpoint | Entregado: /api/v1/matches/explain |
| 7 | Tournament Explainability | Entregado: desglose por senal |
| 8 | Reportes | Entregado: 4 reportes + este documento |

## Metricas Globales

| Metrica | Valor |
|--------|-------|
| Accuracy (192 partidos) | 47.40% |
| Brier Score | 0.660142 |
| Log Loss | 1.091831 |
| RPS | 0.242110 |
| ECE | 0.081351 |

## Pesos Actuales vs Optimos

| Senal | Peso Actual | Peso Optimo Encontrado |
|-------|------------|----------------------|
| elo | 0.4 | 0.2 |
| xg_attack | 0.3 | 0.3 |
| xg_defense | 0.2 | 0.3 |
| fifa | 0.1 | 0.2 |

**Nota:** Los pesos optimos producen metricas identicas a nivel de partido porque solo afectan overall_strength (Monte Carlo), no predict_full.

## Backtesting

| Torneo | Campeon Predicho | Campeon Real | Probabilidad |
|--------|-----------------|-------------|-------------|
| 2014 | Brazil | Germany | 17.0% |
| 2018 | Argentina | France | 13.6% |
| 2022 | France | France | 14.8% |

## Explainability — Drivers

### Nivel de Partido (Brasil vs Argentina)

- **xg_attack**: 36.1%
- **elo**: 28.5%
- **home_advantage**: 25.2%
- **xg_defense**: 9.8%
- **dixon_coles**: 0.5%
- **fifa**: 0.0%

### Nivel de Torneo (Promedio 32 equipos)

- **elo**: 39.8%
- **xg**: 41.5%
- **fifa**: 18.7%
- **other**: 0.0%

## Riesgos Detectados

1. **Sobreconfianza en bins altos**: ECE muestra gaps de 0.36pp en el rango 0.7-0.9 — el modelo predice con mas confianza de la que merece.
2. **xG historico proxy**: Los backtests usan goles promedio como proxy de xG, lo que infla las metricas de calibracion.
3. **Optimizacion de pesos limitada**: El grid search a nivel de partido no discrimina entre combinaciones de pesos. Se necesita optimizacion via Monte Carlo completo.
4. **Sin datos de FIFA historicos**: Los rankings FIFA historicos no estan disponibles en los datos actuales, se estiman desde Elo.

## Recomendaciones para Sprint 4

1. **Reducir bayesian_prior_strength** de 0.5 a ~0.3 para mitigar sobreconfianza en bins altos.
2. **Implementar Platt Scaling** o temperature scaling para calibrar probabilidades posteriores.
3. **Optimizar pesos via Monte Carlo** en un subconjunto reducido de combinaciones (~10-20) con simulaciones de 500-1000 cada una.
4. **Agregar datos reales de xG historicos** (si estan disponibles en fuentes externas) para mejorar backtesting.
5. **Expandir validacion a torneos no-World Cup** (Eurocopa, Copa America) para probar generalizacion.
